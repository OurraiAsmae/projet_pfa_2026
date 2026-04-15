from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional
import httpx, random, sys, os, pickle, numpy as np, warnings
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

MODEL_PATH = "/app/mlops/models/random_forest.pkl"
SCALER_PATH = "/app/mlops/models/scaler.pkl"
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:9999")

# 17 features exactes dans le bon ordre
FEATURE_NAMES = [
    "heure", "jour_semaine", "est_weekend", "montant_mad",
    "type_transaction", "pays_transaction", "est_etranger",
    "tx_lat", "tx_lon", "delta_km", "delta_min_last_tx",
    "nb_tx_1h", "device_type", "est_nouveau_device",
    "age_client", "segment_revenu", "type_carte"
]

state = {
    "model": None, "scaler": None,
    "ml_ok": False, "shap_service": None, "shap_ok": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Démarrage API v3.0...")
    try:
        with open(MODEL_PATH, "rb") as f:
            state["model"] = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            state["scaler"] = pickle.load(f)
        state["ml_ok"] = True
        print(f"✅ RF chargé — {state['model'].n_features_in_} features")
    except Exception as e:
        print(f"⚠️ ML: {e}")

    try:
        from shap_service import SHAPService
        state["shap_service"] = SHAPService()
        state["shap_ok"] = True
        print("✅ SHAP Service prêt")
    except Exception as e:
        print(f"⚠️ SHAP: {e}")
    yield

app = FastAPI(title="Fraud Governance API", version="3.0.0", lifespan=lifespan)

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

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "fraud-governance-api",
        "redis": REDIS_OK,
        "ml_model": state["ml_ok"],
        "shap": state["shap_ok"],
        "version": "3.0.0"
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
        "shap_ok": state["shap_ok"]
    }

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

    # Construire features dict
    features_dict = tx.features or {}
    # Remplir depuis les champs directs de la transaction
    for fname in FEATURE_NAMES:
        if fname not in features_dict:
            features_dict[fname] = getattr(tx, fname, 0.0)

    # Prédiction ML
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
            "shap_hash": shap_cid, "model_id": "RF-v1.0",
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
            "rate_limit_info": rate_info, "velocity_info": velocity_info
        }
        redis_client.mark_as_processed(tx.tx_id, result)
        redis_client.cache_decision(tx.tx_id, result)
    else:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{GATEWAY_URL}/record-decision", json={
                    "tx_id": tx.tx_id, "zone": zone, "shap_hash": shap_cid,
                    "model_id": "RF-v1.0", "card_id": tx.card_id,
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
        rate_limit_info=rate_info, velocity_info=velocity_info
    )

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
