from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional
import httpx, random, sys, os, pickle, numpy as np, warnings
import hashlib, shutil, tempfile, json
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
    if state["model"] and state["scaler"]:
        try:
            X = np.array([[float(features_dict.get(f, 0)) for f in FEATURE_NAMES]])
            X_scaled = state["scaler"].transform(X)
            score = float(state["model"].predict_proba(X_scaled)[0][1])
            ml_used = True
        except Exception as e:
            print(f"⚠️ Prédiction: {e}")

    # Zone routing
    if force_ambigu:
        zone = "AMBIGU"
    elif score > 0.85:
        zone = "FRAUDE"
    elif score < 0.40:
        zone = "LEGITIME"
    else:
        zone = "AMBIGU"

    # SHAP
    shap_cid = f"sha256:{tx.tx_id[:8]}"
    top_features = []
    if state["shap_service"] and ml_used:
        try:
            shap_result = state["shap_service"].compute_shap(features_dict, tx.tx_id)
            shap_cid = shap_result["cid"]
            top_features = shap_result.get("top_features", [])
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

    return DecisionResponse(
        tx_id=tx.tx_id, zone=zone, score=score,
        success=True, blockchain_recorded=blockchain_ok,
        from_cache=False, ml_model_used=ml_used,
        shap_cid=shap_cid, top_features=top_features,
        rate_limit_info=rate_info, velocity_info=velocity_info,
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
