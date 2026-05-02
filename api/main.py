from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional
import httpx, random, sys, os, pickle, numpy as np, warnings
import hashlib, shutil, tempfile, json
import pandas as pd
warnings.filterwarnings("ignore")

sys.path.insert(0, "/app/redis_lib")
sys.path.insert(0, "/app/mlops")

# Redis
try:
    from redis_client import FraudRedisClient
    redis_client = FraudRedisClient()
    REDIS_OK = True
except Exception as e:
    redis_client = None
    REDIS_OK = False

MODELS_DIR = "/app/mlops/models"
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:9999")

# 17 features exactes
FEATURE_NAMES = [
    "heure", "jour_semaine", "est_weekend", "montant_mad",
    "type_transaction", "pays_transaction", "est_etranger",
    "tx_lat", "tx_lon", "delta_km", "delta_min_last_tx",
    "nb_tx_1h", "device_type", "est_nouveau_device",
    "age_client", "segment_revenu", "type_carte"
]

# State global — modele actif peut changer apres deploy
state = {
    "model": None, "scaler": None,
    "ml_ok": False, "shap_service": None, "shap_ok": False,
    "active_model_id": "RF-v1.0",
    "active_model_path": f"{MODELS_DIR}/random_forest.pkl",
    "active_model_type": "RandomForestClassifier"
}

def load_model(model_path: str, scaler_path: str = None):
    """Charge un modele et son scaler depuis le disque"""
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    scaler = None
    sp = scaler_path or f"{MODELS_DIR}/scaler.pkl"
    try:
        with open(sp, "rb") as f:
            scaler = pickle.load(f)
    except:
        pass
    return model, scaler

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Démarrage API v4.0...")

    # Vérifier si un modèle actif est défini dans Redis
    active_path = None
    if redis_client:
        active_info = redis_client.client.get("model:active")
        if active_info:
            info = json.loads(active_info)
            active_path = info.get("model_path")
            state["active_model_id"] = info.get("model_id", "RF-v1.0")
            state["active_model_type"] = info.get("model_type", "RandomForestClassifier")
            print(f"📦 Modèle actif trouvé dans Redis: {state['active_model_id']}")

    # Charger le modèle actif (ou RF par défaut)
    model_path = active_path or f"{MODELS_DIR}/random_forest.pkl"
    try:
        state["model"], state["scaler"] = load_model(model_path)
        state["ml_ok"] = True
        state["active_model_path"] = model_path
        print(f"✅ Modèle chargé: {state['active_model_id']} — {state['model'].n_features_in_} features")
    except Exception as e:
        print(f"⚠️ ML: {e}")

    # SHAP
    try:
        from shap_service import SHAPService
        state["shap_service"] = SHAPService()
        state["shap_ok"] = True
        print("✅ SHAP Service prêt")
    except Exception as e:
        print(f"⚠️ SHAP: {e}")
    yield


# ── RabbitMQ Notifications ────────────────────────────
def publish_rejection_notification(model_id: str, reason: str, 
                                    category: str, rejected_by: str,
                                    role: str):
    """Publish rejection notification to RabbitMQ"""
    try:
        import pika, json
        from datetime import datetime
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="rabbitmq",
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2,
                retry_delay=1))
        channel = connection.channel()
        channel.queue_declare(queue="ds_notifications", durable=True)
        message = {
            "type":        "MODEL_REJECTED",
            "model_id":    model_id,
            "category":    category,
            "reason":      reason,
            "rejected_by": rejected_by,
            "role":        role,
            "timestamp":   datetime.utcnow().isoformat(),
            "read":        False,
        }
        channel.basic_publish(
            exchange="",
            routing_key="ds_notifications",
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2))
        connection.close()
        print(f"✅ Notification sent for {model_id}")
    except Exception as e:
        print(f"⚠️ RabbitMQ notification failed: {e}")


def getTxTime_py():
    from datetime import datetime
    return datetime.utcnow().isoformat()

def publish_amber_alert(tx_data: dict):
    """Publish amber zone transaction to RabbitMQ"""
    try:
        import pika, json
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="rabbitmq",
                credentials=pika.PlainCredentials("guest", "guest"),
                connection_attempts=2,
                retry_delay=1))
        channel = connection.channel()
        channel.queue_declare(queue="amber_alerts", durable=True)
        channel.basic_publish(
            exchange="",
            routing_key="amber_alerts",
            body=json.dumps(tx_data),
            properties=pika.BasicProperties(delivery_mode=2))
        connection.close()
    except Exception as e:
        print(f"⚠️ Amber alert failed: {e}")

app = FastAPI(title="Fraud Governance API", version="4.0.0", lifespan=lifespan)

class Transaction(BaseModel):
    tx_id: str
    montant_mad: float = 1000.0
    card_id: str
    client_id: str
    heure: float = 12.0
    jour_semaine: float = 1.0
    est_weekend: float = 0.0
    type_transaction: float = 0.0
    pays_transaction: float = 0.0
    est_etranger: float = 0.0
    tx_lat: float = 33.57
    tx_lon: float = -7.59
    delta_km: float = 5.0
    delta_min_last_tx: float = 60.0
    nb_tx_1h: float = 1.0
    device_type: float = 0.0
    est_nouveau_device: float = 0.0
    age_client: float = 35.0
    segment_revenu: float = 1.0
    type_carte: float = 0.0
    features: Optional[dict] = None

class DecisionResponse(BaseModel):
    tx_id: str
    zone: str
    score: float
    success: bool
    blockchain_recorded: bool
    from_cache: bool = False
    ml_model_used: bool = False
    shap_cid: Optional[str] = None
    shap_ipfs_url: Optional[str] = None
    shap_pinned: bool = False
    top_features: list = []
    rate_limit_info: dict = {}
    velocity_info: dict = {}
    active_model: str = "RF-v1.0"

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "fraud-governance-api",
        "redis": REDIS_OK,
        "ml_model": state["ml_ok"],
        "shap": state["shap_ok"],
        "version": "4.0.0",
        "active_model": state["active_model_id"]
    }

@app.get("/model/info")
def model_info():
    if not state["model"]:
        raise HTTPException(404, "Aucun modèle chargé")
    return {
        "type": type(state["model"]).__name__,
        "n_estimators": getattr(state["model"], "n_estimators", None),
        "n_features": state["model"].n_features_in_,
        "feature_names": FEATURE_NAMES,
        "classes": state["model"].classes_.tolist(),
        "ml_ok": state["ml_ok"],
        "shap_ok": state["shap_ok"],
        "active_model_id": state["active_model_id"],
        "active_model_path": state["active_model_path"]
    }

@app.get("/model/active")
def get_active_model():
    """Retourne le modèle actuellement actif en production"""
    if redis_client:
        info = redis_client.client.get("model:active")
        if info:
            return json.loads(info)
    return {
        "model_id": state["active_model_id"],
        "model_type": state["active_model_type"],
        "model_path": state["active_model_path"],
        "status": "DEPLOYED"
    }

@app.post("/model/deploy/{model_id}")
async def deploy_model(model_id: str, model_path: str = None):
    """
    Change le modèle actif en production.
    Appelé depuis le Dashboard après Deploy() sur blockchain.
    """
    # Chercher le fichier du modèle
    path = model_path
    if not path:
        # Chercher par nom dans mlops/models/
        import glob
        candidates = glob.glob(f"{MODELS_DIR}/*.pkl")
        for c in candidates:
            if "scaler" not in c and "random_forest" in c.lower():
                path = c
                break
        if not path:
            path = f"{MODELS_DIR}/random_forest.pkl"

    try:
        new_model, new_scaler = load_model(path)

        # Mettre à jour le state en mémoire
        state["model"] = new_model
        state["scaler"] = new_scaler
        state["active_model_id"] = model_id
        state["active_model_path"] = path
        state["active_model_type"] = type(new_model).__name__
        state["ml_ok"] = True

        # Mettre à jour SHAP avec le nouveau modèle
        if state["shap_service"]:
            from shap_service import SHAPService
            state["shap_service"] = SHAPService()

        # Persister dans Redis pour survie aux restarts
        if redis_client:
            redis_client.client.set("model:active", json.dumps({
                "model_id": model_id,
                "model_type": type(new_model).__name__,
                "model_path": path,
                "deployed_at": __import__('datetime').datetime.utcnow().isoformat(),
                "status": "DEPLOYED"
            }))

        print(f"✅ Modèle actif changé vers: {model_id}")
        return {
            "success": True,
            "message": f"Modèle {model_id} maintenant actif en production",
            "model_type": type(new_model).__name__,
            "n_features": new_model.n_features_in_
        }
    except Exception as e:
        raise HTTPException(500, f"Erreur chargement modèle: {e}")

@app.get("/models/available")
def list_available_models():
    """Liste tous les modèles .pkl disponibles dans mlops/models/"""
    import glob
    models = []
    for path in glob.glob(f"{MODELS_DIR}/*.pkl"):
        if "scaler" not in path:
            name = os.path.basename(path).replace(".pkl", "")
            is_active = path == state["active_model_path"]
            models.append({
                "name": name,
                "path": path,
                "size_mb": round(os.path.getsize(path) / 1024 / 1024, 2),
                "is_active": is_active
            })
    return {"models": models, "active_model": state["active_model_id"]}

@app.post("/predict", response_model=DecisionResponse)
async def predict(tx: Transaction):
    # Idempotence
    if redis_client:
        cached = redis_client.get_cached_decision(tx.tx_id)
        if cached:
            return DecisionResponse(**cached, from_cache=True)

    # Rate limiting
    rate_info = {}
    velocity_info = {}
    force_ambigu = False
    if redis_client:
        rate_info = redis_client.check_card_rate_limit(tx.card_id)
        velocity_info = redis_client.check_client_velocity(tx.client_id, tx.montant_mad)
        if rate_info["exceeded"] or velocity_info["suspicious"]:
            force_ambigu = True

    # Features
    features_dict = tx.features or {}
    for fname in FEATURE_NAMES:
        if fname not in features_dict:
            features_dict[fname] = getattr(tx, fname, 0.0)

    # Prédiction avec modèle ACTIF
    score = round(random.uniform(0.1, 0.99), 4)
    ml_used = False
    if state["model"]:
        try:
            X = np.array([[float(features_dict.get(f, 0)) for f in FEATURE_NAMES]])
            # Appliquer scaler seulement si nécessaire (LogisticRegression, SVM)
            model_class = type(state["model"]).__name__
            needs_scaler = any(k in model_class for k in ["Logistic","Linear","SVM","SVR"])
            if needs_scaler and state["scaler"]:
                X_input = state["scaler"].transform(X)
            else:
                X_input = X
            score = float(state["model"].predict_proba(X_input)[0][1])
            ml_used = True
        except Exception as e:
            print(f"⚠️ Prédiction: {e}")

    # Zone routing
    if force_ambigu:
        zone = "AMBIGU"
    elif score > 0.80:
        zone = "FRAUDE"
    elif score < 0.40:
        zone = "LEGITIME"
    else:
        zone = "AMBIGU"

    # SHAP + IPFS automatique
    shap_cid = f"QmSIM{hashlib.sha256(tx.tx_id.encode()).hexdigest()[:38]}"
    shap_ipfs_url = ""
    shap_pinned = False
    top_features = []
    if state["shap_service"] and ml_used:
        try:
            shap_result = state["shap_service"].compute_shap(
                features_dict, tx.tx_id)
            shap_cid      = shap_result.get("cid", shap_cid)
            top_features  = shap_result.get("top_features", [])
            shap_ipfs_url = shap_result.get("ipfs_url", "")
            shap_pinned   = shap_result.get(
                "storage", {}).get("pinned", False)
        except Exception as e:
            print(f"⚠️ SHAP: {e}")

    # Outbox Redis → Blockchain
    blockchain_ok = False
    if redis_client:
        redis_client.push_to_outbox("RECORD_DECISION", {
            "tx_id": tx.tx_id, "zone": zone,
            "shap_hash": shap_cid,
            "model_id": state["active_model_id"],
            "card_id": tx.card_id, "client_id": tx.client_id,
            "score": score, "amount": tx.montant_mad
        })
        blockchain_ok = True
        redis_client.increment_zone_counter(zone)
        result = {
            "tx_id": tx.tx_id, "zone": zone, "score": score,
            "success": True, "blockchain_recorded": blockchain_ok,
            "ml_model_used": ml_used, "shap_cid": shap_cid,
            "top_features": top_features,
            "rate_limit_info": rate_info, "velocity_info": velocity_info,
            "active_model": state["active_model_id"]
        }
        redis_client.mark_as_processed(tx.tx_id, result)
        redis_client.cache_decision(tx.tx_id, result)
    else:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{GATEWAY_URL}/record-decision", json={
                    "tx_id": tx.tx_id, "zone": zone, "shap_hash": shap_cid,
                    "model_id": state["active_model_id"],
                    "card_id": tx.card_id,
                    "client_id": tx.client_id, "score": score
                })
                blockchain_ok = resp.json().get("success", False)
        except Exception as e:
            print(f"Gateway error: {e}")

    # Publish amber alert to RabbitMQ
    if zone == "AMBIGU":
        publish_amber_alert({
            "tx_id":           tx.tx_id,
            "score":           score,
            "montant_mad":     tx.montant_mad,
            "pays_transaction":tx.pays_transaction,
            "device_type":     tx.device_type,
            "heure":           tx.heure,
            "top_features":    top_features,
            "timestamp":       getTxTime_py(),
        })

    return DecisionResponse(
        tx_id=tx.tx_id, zone=zone, score=score,
        success=True, blockchain_recorded=blockchain_ok,
        from_cache=False, ml_model_used=ml_used,
        shap_cid=shap_cid,
        shap_ipfs_url=shap_ipfs_url,
        shap_pinned=shap_pinned,
        top_features=top_features,
        rate_limit_info=rate_info,
        velocity_info=velocity_info,
        active_model=state["active_model_id"]
    )

@app.post("/mlops/upload-dataset")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_name: str = Form(...)
):
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    sha256 = hashlib.sha256(content).hexdigest()
    data_hash = f"sha256:{sha256}"

    import pandas as pd
    df = pd.read_csv(tmp_path)
    fraud_rate = float(df["fraude"].mean()) if "fraude" in df.columns else None

    dest = f"/app/mlops/datasets/{dataset_name}_{sha256[:8]}.csv"
    shutil.copy(tmp_path, dest)
    os.unlink(tmp_path)

    if redis_client:
        redis_client.client.setex(
            f"dataset:{dataset_name}", 86400 * 7,
            json.dumps({
                "dataset_name": dataset_name,
                "data_hash_dvc": data_hash,
                "n_rows": len(df),
                "n_cols": len(df.columns),
                "fraud_rate": fraud_rate,
                "file_path": dest
            })
        )

    return {
        "success": True,
        "dataset_name": dataset_name,
        "data_hash_dvc": data_hash,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "fraud_rate": fraud_rate
    }

@app.get("/shap/{tx_id}")
def get_shap(tx_id: str):
    if not state["shap_service"]:
        raise HTTPException(503, "SHAP Service non disponible")
    cached = redis_client.get_cached_decision(tx_id) if redis_client else None
    cid = cached.get("shap_cid", "") if cached else ""
    result = state["shap_service"].get_shap_from_cid(cid, tx_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@app.get("/transactions/recent")
def get_recent_transactions(limit: int = 50):
    """Get recent transactions from Redis"""
    if not redis_client:
        raise HTTPException(503, "Redis non disponible")
    try:
        # Get recent decisions from Redis
        keys = redis_client.client.keys("decision:*")
        transactions = []
        for key in keys[:limit]:
            data = redis_client.client.get(key)
            if data:
                try:
                    tx = json.loads(data)
                    transactions.append(tx)
                except:
                    pass
        # Sort by timestamp desc
        transactions.sort(
            key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"transactions": transactions[:limit], "total": len(transactions)}
    except Exception as e:
        return {"transactions": [], "total": 0, "error": str(e)}

@app.get("/stats")
def get_stats():
    if not redis_client:
        raise HTTPException(503, "Redis non disponible")
    return redis_client.get_today_stats()

@app.get("/alerts")
def get_alerts():
    if not redis_client:
        raise HTTPException(503, "Redis non disponible")
    return redis_client.get_alerts()

@app.get("/decision/{tx_id}")
def get_decision(tx_id: str):
    if redis_client:
        cached = redis_client.get_cached_decision(tx_id)
        if cached:
            return {"source": "redis_cache", "data": cached}
    return {"source": "blockchain", "tx_id": tx_id}

@app.get("/drift/latest")
def get_drift_latest():
    if not redis_client:
        raise HTTPException(503, "Redis non disponible")
    data = redis_client.client.get("drift:latest")
    if not data:
        return {"status": "no_data", "message": "Aucun rapport drift disponible"}
    return json.loads(data)

@app.get("/drift/history")
def get_drift_history():
    if not redis_client:
        raise HTTPException(503, "Redis non disponible")
    history = redis_client.client.lrange("drift:history", 0, 19)
    return {"history": [json.loads(h) for h in history]}

@app.get("/drift/alerts")
def get_drift_alerts():
    if not redis_client:
        raise HTTPException(503, "Redis non disponible")
    alerts = redis_client.client.lrange("alerts:drift", 0, 9)
    return {"alerts": [json.loads(a) for a in alerts]}

@app.get("/models/submitted")
def get_submitted_models():
    """Retourne les modèles soumis depuis Redis (uploadés via dashboard)"""
    if not redis_client:
        return {"models": []}
    
    # Chercher tous les modèles dans Redis
    keys = redis_client.client.keys("model:submitted:*")
    models = []
    for key in keys:
        data = redis_client.client.get(key)
        if data:
            models.append(json.loads(data))
    
    # Aussi chercher les modèles disponibles sur disque
    import glob
    for path in glob.glob(f"{MODELS_DIR}/*.pkl"):
        if "scaler" not in path:
            name = os.path.basename(path).replace(".pkl", "")
            is_active = path == state["active_model_path"]
            # Vérifier si déjà dans la liste
            if not any(m.get("name") == name for m in models):
                models.append({
                    "name": name,
                    "model_id": f"{name}-v1.0",
                    "path": path,
                    "size_mb": round(os.path.getsize(path)/1024/1024, 2),
                    "is_active": is_active,
                    "status": "DEPLOYED" if is_active else "AVAILABLE",
                    "model_type": "Unknown"
                })
    
    return {"models": models, "active_model": state["active_model_id"]}

@app.get("/datasets/available")
def get_available_datasets():
    """Liste tous les datasets disponibles"""
    datasets = []
    
    # Depuis Redis
    if redis_client:
        keys = redis_client.client.keys("dataset:*")
        for key in keys:
            data = redis_client.client.get(key)
            if data:
                datasets.append(json.loads(data))
    
    # Depuis le disque
    import glob
    for path in glob.glob("/app/mlops/datasets/*.csv"):
        name = os.path.basename(path)
        # Vérifier si déjà dans la liste
        if not any(d.get("file_path") == path or 
                   d.get("dataset_name","") in name for d in datasets):
            try:
                import pandas as pd
                df = pd.read_csv(path, nrows=5)
                sha256 = hashlib.sha256(open(path,"rb").read()).hexdigest()
                datasets.append({
                    "dataset_name": name,
                    "file_path": path,
                    "data_hash_dvc": f"sha256:{sha256}",
                    "n_cols": len(df.columns),
                    "size_mb": round(os.path.getsize(path)/1024/1024, 2)
                })
            except:
                pass
    
    return {"datasets": datasets}

# Override /models/submitted avec vrais types
@app.get("/models/info")
def get_models_info():
    """Retourne les modèles avec leur vrai type chargé depuis le pkl"""
    import glob
    models = []
    for path in glob.glob(f"{MODELS_DIR}/*.pkl"):
        if "scaler" not in path:
            name = os.path.basename(path).replace(".pkl","")
            is_active = path == state["active_model_path"]
            try:
                with open(path,"rb") as f:
                    m = pickle.load(f)
                model_type = type(m).__name__
                n_features = getattr(m,"n_features_in_","N/A")
                n_estimators = getattr(m,"n_estimators","N/A")
            except Exception as e:
                model_type = f"Error: {e}"
                n_features = "N/A"
                n_estimators = "N/A"
            models.append({
                "name": name,
                "model_id": f"{name}-v1.0",
                "path": path,
                "size_mb": round(os.path.getsize(path)/1024/1024,2),
                "is_active": is_active,
                "status": "DEPLOYED" if is_active else "AVAILABLE",
                "model_type": model_type,
                "n_features": n_features,
                "n_estimators": n_estimators
            })
    return {"models": models, "active_model": state["active_model_id"]}

import subprocess


def peer_query_local(function: str, args: list, msp_user: str = "Admin@bank.fraud-governance.com") -> dict:
    """Appelle le peer chaincode query depuis l'API"""
    crypto_path = "/home/asmae/fraud-governance-system/blockchain/network/crypto-material"
    fabric_cfg  = "/home/asmae/fraud-governance-system/blockchain/network"
    peer_bin    = "/usr/local/bin/peer"
    args_json   = json.dumps({"function": function, "Args": args})
    cmd = [peer_bin, "chaincode", "query",
        "-C", "modelgovernance",
        "-n", "model-governance-cc",
        "-c", args_json
    ]
    env = {
        "FABRIC_CFG_PATH": fabric_cfg,
        "CORE_PEER_TLS_ENABLED": "true",
        "CORE_PEER_LOCALMSPID": "BankMSP",
        "CORE_PEER_MSPCONFIGPATH": f"{crypto_path}/peerOrganizations/bank.fraud-governance.com/users/{msp_user}/msp",
        "CORE_PEER_ADDRESS": "peer0.bank.fraud-governance.com:7051",
        "CORE_PEER_TLS_ROOTCERT_FILE": f"{crypto_path}/peerOrganizations/bank.fraud-governance.com/peers/peer0.bank.fraud-governance.com/tls/ca.crt",
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    }
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout.strip())
                return {"success": True, "data": data}
            except:
                return {"success": True, "data": result.stdout.strip()}
        else:
            return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}

def peer_invoke_local(function: str, args: list, msp_user: str = "Admin@bank.fraud-governance.com") -> dict:
    """Appelle le peer chaincode invoke depuis l'API"""
    crypto_path = "/home/asmae/fraud-governance-system/blockchain/network/crypto-material"
    fabric_cfg = "/home/asmae/fraud-governance-system/blockchain/network"
    peer_bin = "/usr/local/bin/peer"
    
    args_json = json.dumps({"function": function, "Args": args})
    
    cmd = [peer_bin, "chaincode", "invoke",
        "-o", "orderer.fraud-governance.com:7050",
        "-C", "modelgovernance",
        "-n", "model-governance-cc",
        "--tls",
        "--cafile", f"{crypto_path}/ordererOrganizations/fraud-governance.com/orderers/orderer.fraud-governance.com/tls/ca.crt",
        "--peerAddresses", "peer0.bank.fraud-governance.com:7051",
        "--tlsRootCertFiles", f"{crypto_path}/peerOrganizations/bank.fraud-governance.com/peers/peer0.bank.fraud-governance.com/tls/ca.crt",
        "-c", args_json
    ]
    
    env = {
        "FABRIC_CFG_PATH": fabric_cfg,
        "CORE_PEER_TLS_ENABLED": "true",
        "CORE_PEER_LOCALMSPID": "BankMSP",
        "CORE_PEER_MSPCONFIGPATH": f"{crypto_path}/peerOrganizations/bank.fraud-governance.com/users/{msp_user}/msp",
        "CORE_PEER_ADDRESS": "peer0.bank.fraud-governance.com:7051",
        "CORE_PEER_TLS_ROOTCERT_FILE": f"{crypto_path}/peerOrganizations/bank.fraud-governance.com/peers/peer0.bank.fraud-governance.com/tls/ca.crt",
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    }
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
    success = result.returncode == 0
    return {"success": success, "output": result.stdout + result.stderr}

@app.post("/governance/validate-compliance/{model_id}")
async def api_validate_compliance(model_id: str):
    """Validate compliance via peer depuis l'API"""
    result = peer_invoke_local(
        "ValidateCompliance",
        [model_id, "User2@bank.fraud-governance.com"],
        "User2@bank.fraud-governance.com"
    )
    return result

@app.post("/governance/approve-technical/{model_id}")
async def api_approve_technical(model_id: str):
    """Approve technical via peer depuis l'API"""
    result = peer_invoke_local(
        "ApproveTechnical",
        [model_id, "User3@bank.fraud-governance.com"],
        "User3@bank.fraud-governance.com"
    )
    return result

@app.post("/governance/deploy/{model_id}")
async def api_deploy_model(model_id: str):
    """Deploy model via peer depuis l'API"""
    result = peer_invoke_local(
        "Deploy",
        [model_id, "Admin@bank.fraud-governance.com"],
        "Admin@bank.fraud-governance.com"
    )
    return result

@app.post("/governance/revoke/{model_id}")
async def api_revoke_model(model_id: str, reason: str = "Revoked"):
    """Revoke model via peer depuis l'API"""
    result = peer_invoke_local(
        "RevokeModel",
        [model_id, reason],
        "Admin@bank.fraud-governance.com"
    )
    return result

@app.post("/governance/reject/{model_id}")
async def api_reject_model(model_id: str, reason: str = "Rejected", category: str = "Compliance", signer: str = "User2@bank.fraud-governance.com"):
    """Reject model via peer - Compliance Officer (User2) ou ML Engineer (User3)"""
    result = peer_invoke_local(
        "RejectModel",
        [model_id, reason, category],
        signer
    )
    if result.get("success"):
        role = "Compliance Officer" if "User2" in signer else "ML Engineer"
        publish_rejection_notification(
            model_id=model_id,
            reason=reason,
            category=category,
            rejected_by=signer.split("@")[0],
            role=role)
    return result



@app.get("/governance/history/{model_id}")
async def get_model_history(model_id: str):
    """Get full blockchain history for a model"""
    result = peer_query_local(
        "GetModelHistory",
        [model_id],
        "Admin@bank.fraud-governance.com"
    )
    return result

@app.get("/governance/all-models")
async def get_all_models():
    """Get all models from blockchain dynamically"""
    result = peer_query_local(
        "GetAllModels", [],
        "Admin@bank.fraud-governance.com"
    )
    if result.get("success"):
        try:
            data = result.get("data", [])
            if isinstance(data, str):
                data = json.loads(data)
            if not data:
                data = []
            return {"models": data, "total": len(data)}
        except Exception as e:
            return {"models": [], "total": 0, "error": str(e)}
    return {"models": [], "total": 0, "error": result.get("error", "")}

@app.get("/governance/model/{model_id}")
async def api_get_model(model_id: str):
    """Get model status depuis blockchain"""
    crypto_path = "/home/asmae/fraud-governance-system/blockchain/network/crypto-material"
    fabric_cfg = "/home/asmae/fraud-governance-system/blockchain/network"
    peer_bin = "/usr/local/bin/peer"
    
    args_json = json.dumps({"function": "GetModel", "Args": [model_id]})
    cmd = [peer_bin, "chaincode", "query",
        "-C", "modelgovernance", "-n", "model-governance-cc",
        "-c", args_json
    ]
    env = {
        "FABRIC_CFG_PATH": fabric_cfg,
        "CORE_PEER_TLS_ENABLED": "true",
        "CORE_PEER_LOCALMSPID": "BankMSP",
        "CORE_PEER_MSPCONFIGPATH": f"{crypto_path}/peerOrganizations/bank.fraud-governance.com/users/Admin@bank.fraud-governance.com/msp",
        "CORE_PEER_ADDRESS": "peer0.bank.fraud-governance.com:7051",
        "CORE_PEER_TLS_ROOTCERT_FILE": f"{crypto_path}/peerOrganizations/bank.fraud-governance.com/peers/peer0.bank.fraud-governance.com/tls/ca.crt",
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    }
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
    if result.returncode == 0:
        return json.loads(result.stdout)
    return {"error": result.stderr}

# ── IPFS Integration ─────────────────────────────────
try:
    from ipfs_client import IPFSClient
    ipfs_client = IPFSClient()
    IPFS_OK = ipfs_client.test_connection()
    if IPFS_OK:
        print("✅ IPFS Pinata connecté")
    else:
        print("⚠️ IPFS non disponible — mode simulé")
except Exception as e:
    ipfs_client = None
    IPFS_OK = False
    print(f"⚠️ IPFS: {e}")

@app.get("/ipfs/list")
def list_ipfs_files():
    """Liste tous les fichiers pinnés sur IPFS Pinata"""
    if not ipfs_client:
        raise HTTPException(503, "IPFS non disponible")
    files = ipfs_client.list_pinned(50)
    return {"files": files, "total": len(files)}

@app.get("/ipfs/get/{cid}")
def get_ipfs_content(cid: str):
    """Récupère le contenu d'un CID depuis IPFS"""
    if not ipfs_client:
        raise HTTPException(503, "IPFS non disponible")
    content = ipfs_client.get_from_ipfs(cid)
    if not content:
        raise HTTPException(404, f"CID {cid} non trouvé")
    return content

@app.post("/ipfs/pin-model-card")
async def pin_model_card(
    model_id: str,
    model_type: str,
    auc_roc: float = 0.0,
    f1: float = 0.0,
    precision: float = 0.0,
    recall: float = 0.0,
    dataset_name: str = "",
    dataset_hash: str = "",
    submitted_by: str = "system"
):
    """Crée et pine une Model Card sur IPFS"""
    if not ipfs_client:
        # Fallback simulé
        import hashlib
        fake_cid = "QmSIM" + hashlib.sha256(
            model_id.encode()).hexdigest()[:38]
        return {"cid": fake_cid, "pinned": False}

    result = ipfs_client.create_model_card(
        model_id=model_id,
        model_type=model_type,
        metrics={"auc_roc": auc_roc, "f1": f1,
                 "precision": precision, "recall": recall},
        dataset_info={"name": dataset_name,
                      "hash": dataset_hash},
        feature_names=FEATURE_NAMES,
        submitted_by=submitted_by
    )
    return {
        "cid": result["cid"],
        "ipfs_url": result["ipfs_url"],
        "local_path": result["local_path"],
        "pinned": result["pinned"]
    }

@app.get("/ipfs/health")
def ipfs_health():
    ok = ipfs_client.test_connection() if ipfs_client else False
    return {"status": "ok" if ok else "unavailable",
            "pinata": ok}

# ── Dataset Governance Endpoints ─────────────────────
from dataset_service import dataset_svc
import io

@app.post("/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_name: str = Form(...),
    uploaded_by: str = Form("data.scientist1")
):
    """
    Complete Dataset Governance Upload:
    Step 1 → Hash + Versioning
    Step 2 → Dataset Card → IPFS
    Step 3 → Feature Analysis + Quality
    Step 4 → Local Storage
    Step 5 → Blockchain + Lineage
    """
    content = await file.read()

    # Step 1 — Hash + Version
    hash_val = dataset_svc.compute_hash(content)
    duplicate = dataset_svc.check_duplicate(hash_val)
    if duplicate:
        return {
            "success": False,
            "message": "Dataset already exists",
            "existing": duplicate
        }
    version = dataset_svc.get_next_version(dataset_name)

    # Load DataFrame
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(400, f"Invalid CSV: {e}")

    # Step 2 — Dataset Card → IPFS
    card = dataset_svc.create_dataset_card(
        dataset_name, version, hash_val,
        df, uploaded_by)
    dataset_id = card["identity"]["dataset_id"]
    card_cid   = dataset_svc.pin_dataset_card(
        card, dataset_id)
    card["identity"]["cid_ipfs"] = card_cid

    # Step 3 — Feature Analysis + Quality
    analysis = dataset_svc.analyze_features(df, dataset_id)
    analysis_cid = dataset_svc.pin_analysis(
        analysis, dataset_id)

    # Step 4 — Local Storage
    paths = dataset_svc.save_locally(
        content, df, dataset_name, version,
        hash_val, card, analysis,
        card_cid, analysis_cid)

    # Step 5 — Blockchain
    bc_ok = dataset_svc.register_on_blockchain(
        dataset_id=dataset_id,
        hash_val=hash_val,
        card_cid=card_cid,
        version=version,
        n_rows=card["statistics"]["n_rows"],
        fraud_rate=card["statistics"]["fraud_rate"],
        quality_score=analysis["quality"]["total_score"],
        uploaded_by=uploaded_by
    )

    # Update meta with blockchain status
    try:
        meta = json.load(open(paths["meta_path"]))
        meta["blockchain_registered"] = bc_ok
        meta["card_cid"] = card_cid
        meta["analysis_cid"] = analysis_cid
        json.dump(meta, open(paths["meta_path"],"w"), indent=2)
    except:
        pass

    return {
        "success":          True,
        "dataset_id":       dataset_id,
        "name":             dataset_name,
        "version":          version,
        "hash":             hash_val,
        "card_cid":         card_cid,
        "analysis_cid":     analysis_cid,
        "card_ipfs_url":    f"https://gateway.pinata.cloud/ipfs/{card_cid}",
        "n_rows":           card["statistics"]["n_rows"],
        "n_cols":           card["statistics"]["n_columns"],
        "fraud_rate":       card["statistics"]["fraud_rate"],
        "quality_score":    analysis["quality"]["total_score"],
        "quality_rating":   analysis["quality"]["rating"],
        "blockchain":       "✅ Registered" if bc_ok
                            else "⚠️ Pending",
        "top_features":     analysis["feature_importance"][:5],
        "top_correlations": analysis["correlations"][:5],
        "local_path":       paths["csv_path"]
    }

@app.get("/datasets/list")
def list_datasets():
    """List all datasets with metadata"""
    datasets = dataset_svc.get_all_datasets()
    return {"datasets": datasets, "total": len(datasets)}

@app.get("/datasets/available")
def datasets_available():
    """Available datasets for model training"""
    datasets = dataset_svc.get_all_datasets()
    return {"datasets": datasets}

@app.get("/datasets/{dataset_id}/analysis")
def get_dataset_analysis(dataset_id: str):
    """Get complete feature analysis"""
    analysis = dataset_svc.get_dataset_analysis(dataset_id)
    if not analysis:
        raise HTTPException(404, "Analysis not found")
    return analysis

@app.get("/datasets/{dataset_id}/lineage")
def get_dataset_lineage(dataset_id: str):
    """Get dataset lineage — which models use this dataset"""
    return dataset_svc.get_lineage(dataset_id)

@app.get("/datasets/compare/{id1}/{id2}")
def compare_datasets(id1: str, id2: str):
    """Compare two dataset versions"""
    return dataset_svc.compare_versions(id1, id2)

@app.post("/datasets/{dataset_id}/link-model")
def link_model(dataset_id: str, model_id: str):
    """Link a model to its training dataset"""
    ok = dataset_svc.link_model_to_dataset(
        model_id, dataset_id,
        dataset_svc._get_meta(dataset_id,
                             ).get("hash","") 
        if dataset_svc._get_meta(dataset_id) else "")
    return {"success": ok, "lineage":
            f"{model_id} → {dataset_id}"}

@app.post("/ipfs/pin-json")
async def pin_json_to_ipfs(request: dict):
    """Pin any JSON to IPFS Pinata — fallback to Redis if limit reached"""
    data = request.get("data", {})
    name = request.get("name", "blockmlgov-data")
    
    # Try IPFS first
    if ipfs_client:
        cid = ipfs_client.pin_json(data, name)
        if cid:
            return {
                "cid": cid,
                "url": f"https://gateway.pinata.cloud/ipfs/{cid}",
                "pinned": True
            }
    
    # Fallback: store in Redis with fake CID
    import hashlib, json as _json
    content_hash = hashlib.sha256(
        _json.dumps(data, sort_keys=True).encode()).hexdigest()
    fake_cid = f"LOCAL-{content_hash[:40]}"
    
    if redis_client:
        redis_client.client.setex(
            f"ipfs:{fake_cid}",
            86400 * 30,  # 30 days
            _json.dumps({"name": name, "content": data}))
        # Add to list
        redis_client.client.lpush("ipfs:pins", _json.dumps({
            "cid": fake_cid, "name": name, "size": len(_json.dumps(data))
        }))
    
    return {
        "cid":    fake_cid,
        "url":    f"local://{fake_cid}",
        "pinned": True,
        "storage": "redis_fallback"
    }

@app.post("/governance/submit-model")
async def governance_submit_model(request: dict):
    """Submit model to blockchain via peer binary"""
    import subprocess
    crypto = "/home/asmae/fraud-governance-system/blockchain/network/crypto-material"
    fabric_cfg = "/home/asmae/fraud-governance-system/blockchain/network"
    peer_bin = "/usr/local/bin/peer"

    model_id     = request.get("model_id","")
    version      = request.get("version","1.0")
    data_hash    = request.get("data_hash","")
    mlflow_run   = request.get("mlflow_run_id","")
    card_cid     = request.get("model_card_cid","")
    auc          = request.get("auc","0")
    f1           = request.get("f1","0")
    precision    = request.get("precision","0")
    recall       = request.get("recall","0")

    args_json = json.dumps({
        "function": "SubmitModel",
        "Args": [model_id, version, data_hash,
                 mlflow_run, card_cid,
                 auc, f1, precision, recall]
    })

    cmd = [peer_bin, "chaincode", "invoke",
        "-o", "orderer.fraud-governance.com:7050",
        "-C", "modelgovernance",
        "-n", "model-governance-cc",
        "--tls",
        "--cafile",
        f"{crypto}/ordererOrganizations/fraud-governance.com/orderers/orderer.fraud-governance.com/tls/ca.crt",
        "--peerAddresses", "peer0.bank.fraud-governance.com:7051",
        "--tlsRootCertFiles",
        f"{crypto}/peerOrganizations/bank.fraud-governance.com/peers/peer0.bank.fraud-governance.com/tls/ca.crt",
        "-c", args_json
    ]

    env = {
        "FABRIC_CFG_PATH": fabric_cfg,
        "CORE_PEER_TLS_ENABLED": "true",
        "CORE_PEER_LOCALMSPID": "BankMSP",
        "CORE_PEER_MSPCONFIGPATH":
            f"{crypto}/peerOrganizations/bank.fraud-governance.com/users/Admin@bank.fraud-governance.com/msp",
        "CORE_PEER_ADDRESS": "peer0.bank.fraud-governance.com:7051",
        "CORE_PEER_TLS_ROOTCERT_FILE":
            f"{crypto}/peerOrganizations/bank.fraud-governance.com/peers/peer0.bank.fraud-governance.com/tls/ca.crt",
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    }

    try:
        result = subprocess.run(
            cmd, env=env,
            capture_output=True, text=True, timeout=30)
        success = result.returncode == 0
        output  = result.stdout + result.stderr

        # Check if already exists
        if "existe deja" in output or "already exists" in output:
            return {"success": True,
                    "message": "Model already registered",
                    "output": output}

        return {"success": success,
                "message": "Model submitted to blockchain"
                           if success else "Failed",
                "output": output[:200]}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/shap/global")
async def compute_global_shap(request: dict):
    """
    Compute Global SHAP for a model
    on training dataset sample
    Pin result to IPFS
    """
    model_path = request.get("model_path","")
    dataset_id = request.get("dataset_id","")
    model_id   = request.get("model_id","")
    run_id     = request.get("run_id","")

    if not model_path or not os.path.exists(model_path):
        raise HTTPException(404,
            f"Model not found: {model_path}")

    try:
        # Load model
        with open(model_path,"rb") as f:
            model = pickle.load(f)
        model_type = type(model).__name__

        # Load model_loader for SHAP type
        from model_loader import (
            get_shap_explainer_type,
            create_shap_explainer,
            compute_global_shap as compute_gs
        )
        shap_type = get_shap_explainer_type(model_type)

        # Load dataset sample
        DATASETS_DIR = "/app/mlops/datasets"
        X_sample = None
        feature_names = [
            "heure","jour_semaine","est_weekend",
            "montant_mad","type_transaction",
            "pays_transaction","est_etranger",
            "tx_lat","tx_lon","delta_km",
            "delta_min_last_tx","nb_tx_1h",
            "device_type","est_nouveau_device",
            "age_client","segment_revenu","type_carte"
        ]

        if dataset_id and os.path.exists(DATASETS_DIR):
            for f in os.listdir(DATASETS_DIR):
                if not f.endswith("_meta.json"):
                    continue
                meta = json.load(
                    open(f"{DATASETS_DIR}/{f}"))
                if meta.get("dataset_id") == dataset_id:
                    csv_p = meta.get("csv_path","")
                    if os.path.exists(csv_p):
                        df_data = pd.read_csv(csv_p)
                        # Filter only feature columns
                        cols = [c for c in feature_names
                               if c in df_data.columns]
                        if cols:
                            df_feat = df_data[cols].copy()
                            # Encode categorical columns
                            for col in df_feat.columns:
                                if df_feat[col].dtype == object:
                                    df_feat[col] = pd.Categorical(
                                        df_feat[col]).codes
                            df_feat = df_feat.fillna(0)
                            # Use scaler if available
                            try:
                                scaler_path = "/app/mlops/models/scaler.pkl"
                                if os.path.exists(scaler_path):
                                    with open(scaler_path,"rb") as sf:
                                        scaler = pickle.load(sf)
                                    X_sample = scaler.transform(
                                        df_feat.sample(
                                            min(500, len(df_feat)),
                                            random_state=42).values)
                                else:
                                    X_sample = df_feat.sample(
                                        min(500, len(df_feat)),
                                        random_state=42).values
                            except:
                                X_sample = df_feat.sample(
                                    min(500, len(df_feat)),
                                    random_state=42).values
                            feature_names = cols
                        break

        if X_sample is None:
            # Use synthetic data as fallback
            X_sample = np.random.randn(
                200, len(feature_names))

        # Compute Global SHAP
        result = compute_gs(
            model, model_type,
            X_sample, feature_names)

        if result.get("error"):
            raise HTTPException(500, result["error"])

        # Pin to IPFS
        cid = ""
        if ipfs_client:
            summary = {
                "model_id":         model_id,
                "model_type":       model_type,
                "run_id":           run_id,
                "dataset_id":       dataset_id,
                "n_samples":        len(X_sample),
                "explainer_type":   shap_type,
                "global_importance":result["global_importance"],
                "top_5_features":   result["top_5_features"],
                "computed_at":      result["computed_at"]
            }
            cid = ipfs_client.pin_json(
                summary,
                f"global-shap-{model_id}")

        result["cid"]      = cid or ""
        result["ipfs_url"] = (
            f"https://gateway.pinata.cloud/ipfs/{cid}"
            if cid else "")
        result["model_type"]  = model_type
        result["model_id"]    = model_id
        result["n_features"]  = len(feature_names)
        result["n_samples"]   = len(X_sample)
        result["explainer_type"] = shap_type

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/model/hash")
def compute_model_hash(path: str):
    """Compute SHA256 hash of a model file"""
    if not os.path.exists(path):
        raise HTTPException(404, f"File not found: {path}")
    import hashlib
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return {
        "path": path,
        "hash": f"sha256:{sha.hexdigest()}",
        "size": os.path.getsize(path)
    }



@app.post("/model/evaluate-upload")
async def evaluate_model_upload(
    file: UploadFile = File(...),
    dataset_id: str = "",
    dataset_path: str = ""):
    """Evaluate uploaded pkl model on test data"""
    import pickle, hashlib, tempfile, glob, re
    import pandas as pd
    from sklearn.metrics import (
        roc_auc_score, f1_score,
        precision_score, recall_score,
        average_precision_score)

    # Resolve dataset path
    datasets_dir = "/app/mlops/datasets"
    if not dataset_path:
        if dataset_id:
            hash_match = re.search(r"([a-f0-9]{8})", dataset_id)
            if hash_match:
                h = hash_match.group(1)
                matches = glob.glob(f"{datasets_dir}/*{h}*.csv")
                dataset_path = matches[0] if matches else ""
        if not dataset_path:
            dataset_path = f"{datasets_dir}/transactions_bancaires_v2_9adb21e7.csv"

    # Save uploaded file to temp
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            model = pickle.load(f)

        if not os.path.exists(dataset_path):
            raise HTTPException(404, f"Dataset not found: {dataset_path}")

        df = pd.read_csv(dataset_path)
        target_col = "fraude" if "fraude" in df.columns else "is_fraud"
        if target_col not in df.columns:
            raise HTTPException(400, f"Target column not found")

        feature_cols = [
            "heure", "jour_semaine", "est_weekend", "montant_mad",
            "type_transaction", "pays_transaction", "est_etranger",
            "tx_lat", "tx_lon", "delta_km", "delta_min_last_tx",
            "nb_tx_1h", "device_type", "est_nouveau_device",
            "age_client", "segment_revenu", "type_carte"
        ]
        available = [c for c in feature_cols if c in df.columns]
        X = df[available].copy()
        y = df[target_col]

        for col in X.select_dtypes(include="object").columns:
            X[col] = pd.Categorical(X[col]).codes
        X = X.fillna(0)

        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y)

        X_eval = X_test.copy()
        model_class = type(model).__name__
        if "Logistic" in model_class or "Linear" in model_class:
            scaler_path = "/app/mlops/models/scaler.pkl"
            if os.path.exists(scaler_path):
                import pickle as _pkl
                with open(scaler_path, "rb") as _f:
                    _scaler = _pkl.load(_f)
                X_eval = pd.DataFrame(_scaler.transform(X_eval), columns=X_eval.columns)
        y_proba = model.predict_proba(X_eval)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_eval)

        # Optimal threshold
        from sklearn.metrics import precision_recall_curve
        prec_arr, rec_arr, thresholds = precision_recall_curve(y_test, y_proba)
        f1_arr = 2 * prec_arr * rec_arr / (prec_arr + rec_arr + 1e-8)
        best_thresh = thresholds[f1_arr[:-1].argmax()] if len(thresholds) > 0 else 0.5
        y_pred = (y_proba >= best_thresh).astype(int)

        auc_roc   = round(float(roc_auc_score(y_test, y_proba)), 4)
        auc_pr    = round(float(average_precision_score(y_test, y_proba)), 4)
        f1        = round(float(f1_score(y_test, y_pred)), 4)
        precision = round(float(precision_score(y_test, y_pred, zero_division=0)), 4)
        recall    = round(float(recall_score(y_test, y_pred, zero_division=0)), 4)

        sha = hashlib.sha256(content)
        model_hash = f"sha256:{sha.hexdigest()}"

        return {
            "success":       True,
            "auc_roc":       auc_roc,
            "auc_pr":        auc_pr,
            "f1":            f1,
            "precision":     precision,
            "recall":        recall,
            "n_train":       len(X_train),
            "n_test":        len(X_test),
            "model_hash":    model_hash,
            "features_used": len(available),
            "threshold":     round(float(best_thresh), 4),
            "dataset_used":  dataset_path.split("/")[-1],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Evaluation error: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.post("/model/deactivate")
async def deactivate_model(request: dict):
    """Deactivate current model — clear Redis + global"""
    global active_model_id
    model_id = request.get("model_id","")
    try:
        # Clear Redis active model
        redis_client.delete("active_model")
        redis_client.delete("active_model_id")
        # Clear global
        active_model_id = None
        return {
            "success": True,
            "message": f"Model {model_id} deactivated",
            "active_model": None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
