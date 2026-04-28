"""
Kafka Consumer — Lit les transactions depuis Kafka
et appelle l'API predict pour scoring en temps réel
"""
import json
import time
import logging
import httpx
from kafka import KafkaConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

import os
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC        = "fraud-transactions"
GROUP_ID     = "fraud-detection-group"
API_URL      = os.getenv("API_URL", "http://localhost:8000")

STATS = {"total": 0, "FRAUDE": 0, "AMBIGU": 0, "LEGITIME": 0, "errors": 0}

def predict_transaction(tx: dict) -> dict:
    """Appelle l'API predict"""
    try:
        payload = {k: v for k, v in tx.items()
                  if k not in ["timestamp", "pattern"]}
        r = httpx.post(
            f"{API_URL}/predict",
            json=payload,
            timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            log.error(f"API error {r.status_code}: {r.text[:100]}")
            return {}
    except Exception as e:
        log.error(f"Predict error: {e}")
        return {}

def main():
    log.info(f"🚀 Starting Kafka Consumer")
    log.info(f"   Broker: {KAFKA_BROKER}")
    log.info(f"   Topic:  {TOPIC}")
    log.info(f"   Group:  {GROUP_ID}")

    consumer = None
    for attempt in range(30):
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=KAFKA_BROKER,
                group_id=GROUP_ID,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="latest",
                enable_auto_commit=True,
            )
            log.info(f"✅ Connected to Kafka on attempt {attempt+1}")
            break
        except Exception as e:
            log.info(f"⏳ Waiting for Kafka... attempt {attempt+1}/30")
            time.sleep(5)
    if consumer is None:
        raise Exception("❌ Could not connect to Kafka")

    log.info("✅ Connected to Kafka — waiting for transactions...")

    for message in consumer:
        tx = message.value
        tx_id = tx.get("tx_id", "?")
        pattern = tx.get("pattern", "?")

        # Score via API
        result = predict_transaction(tx)

        if result:
            zone  = result.get("zone", "?")
            score = result.get("score", 0)
            STATS["total"] += 1
            STATS[zone] = STATS.get(zone, 0) + 1

            icon = {"FRAUDE":"🔴","AMBIGU":"🟡","LEGITIME":"🟢"}.get(zone,"⚪")
            log.info(
                f"{icon} {tx_id} | Score: {score:.4f} | "
                f"Zone: {zone} | Pattern: {pattern} | "
                f"Stats: F={STATS['FRAUDE']} "
                f"A={STATS['AMBIGU']} "
                f"L={STATS['LEGITIME']}")
        else:
            STATS["errors"] += 1
            log.warning(f"⚠️ Failed to score {tx_id}")

if __name__ == "__main__":
    main()
