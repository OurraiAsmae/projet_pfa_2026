import sys
import time
import json
import logging
import os
import httpx

sys.path.insert(0, "/app/redis_lib")
from redis_client import FraudRedisClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:9999")

def send_to_fabric(event: dict) -> bool:
    payload = event.get("payload", {})
    event_type = event.get("event_type", "")
    try:
        if event_type == "RECORD_DECISION":
            resp = httpx.post(f"{GATEWAY_URL}/record-decision", json={
                "tx_id": payload["tx_id"],
                "zone": payload["zone"],
                "shap_hash": payload["shap_hash"],
                "model_id": payload["model_id"],
                "card_id": payload["card_id"],
                "client_id": payload["client_id"],
                "score": payload["score"]
            }, timeout=15.0)
            return resp.json().get("success", False)
        elif event_type == "SUBMIT_MODEL":
            resp = httpx.post(f"{GATEWAY_URL}/submit-model", json=payload, timeout=15.0)
            return resp.json().get("success", False)
        return False
    except Exception as e:
        log.error(f"Erreur Gateway: {e}")
        return False

def run():
    log.info(f"🚀 Governance Processor — Gateway: {GATEWAY_URL}")
    redis = FraudRedisClient()
    stats = {"processed": 0, "failed": 0}

    while True:
        try:
            event = redis.pop_from_outbox(timeout=1)
            if not event:
                continue
            event_id = event.get("event_id", "unknown")
            tx_id = event.get("payload", {}).get("tx_id", "unknown")
            log.info(f"📦 {event_id} — tx {tx_id}")
            success = send_to_fabric(event)
            if success:
                redis.mark_outbox_success(event_id, event)
                stats["processed"] += 1
                log.info(f"✅ {tx_id} → blockchain")
            else:
                redis.mark_outbox_failed(event_id, "Gateway error", event)
                stats["failed"] += 1
                log.warning(f"⚠️ {tx_id} retry {event.get('attempts',0)+1}/3")
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.error(f"Erreur: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run()
