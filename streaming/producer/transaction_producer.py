"""
Transaction Producer — Génère des transactions bancaires réalistes avec Faker
et les publie sur Kafka topic: fraud-transactions
"""
import json
import time
import random
import argparse
from datetime import datetime
from kafka import KafkaProducer
from faker import Faker

fake = Faker('fr_FR')

import os
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC        = "fraud-transactions"

# Configs de fraude pour simuler différents patterns
FRAUD_PATTERNS = [
    # Pattern 1: Transaction normale (légitime)
    {
        "name": "normal",
        "weight": 0.7,
        "montant_range": (50, 2000),
        "heure_range": (8, 22),
        "est_etranger": 0,
        "est_nouveau_device": 0,
        "delta_km_range": (0, 10),
        "nb_tx_1h_range": (1, 3),
    },
    # Pattern 2: Fraude évidente
    {
        "name": "fraud_obvious",
        "weight": 0.1,
        "montant_range": (5000, 50000),
        "heure_range": (0, 5),
        "est_etranger": 1,
        "est_nouveau_device": 1,
        "delta_km_range": (500, 5000),
        "nb_tx_1h_range": (5, 20),
    },
    # Pattern 3: Fraude subtile (amber zone)
    {
        "name": "fraud_subtle",
        "weight": 0.2,
        "montant_range": (1000, 8000),
        "heure_range": (1, 7),
        "est_etranger": 0,
        "est_nouveau_device": 1,
        "delta_km_range": (50, 200),
        "nb_tx_1h_range": (3, 8),
    },
]

PAYS_MAP    = {"MA": 0, "FR": 1, "ES": 2, "US": 3, "GB": 4, "DE": 5}
DEVICE_MAP  = {"mobile": 0, "web": 1, "atm": 2, "pos": 3}
PAYS_LIST   = list(PAYS_MAP.keys())
DEVICE_LIST = list(DEVICE_MAP.keys())

def generate_transaction(pattern: dict) -> dict:
    now = datetime.utcnow()
    heure = random.randint(*pattern["heure_range"])
    jour  = now.weekday()
    pays  = "MA" if not pattern["est_etranger"] else random.choice(["FR","ES","US","GB"])

    tx = {
        "tx_id":             f"TX-{int(time.time()*1000)}-{random.randint(1000,9999)}",
        "card_id":           f"CARD-{random.randint(1000,9999)}",
        "client_id":         f"CLIENT-{random.randint(100,999)}",
        "timestamp":         now.isoformat(),
        "montant_mad":       round(random.uniform(*pattern["montant_range"]), 2),
        "heure":             float(heure),
        "jour_semaine":      float(jour),
        "est_weekend":       float(1 if jour >= 5 else 0),
        "type_transaction":  float(random.randint(0, 3)),
        "pays_transaction":  float(PAYS_MAP.get(pays, 0)),
        "est_etranger":      float(pattern["est_etranger"]),
        "tx_lat":            round(random.uniform(28, 36), 4),
        "tx_lon":            round(random.uniform(-13, -1), 4),
        "delta_km":          round(random.uniform(*pattern["delta_km_range"]), 2),
        "delta_min_last_tx": round(random.uniform(1, 120), 2),
        "nb_tx_1h":          float(random.randint(*pattern["nb_tx_1h_range"])),
        "device_type":       float(DEVICE_MAP.get(random.choice(DEVICE_LIST), 0)),
        "est_nouveau_device":float(pattern["est_nouveau_device"]),
        "age_client":        float(random.randint(18, 75)),
        "segment_revenu":    float(random.randint(1, 3)),
        "type_carte":        float(random.randint(1, 3)),
        "pattern":           pattern["name"],
    }
    return tx

def main(rate: float = float(os.getenv("RATE","1.0")), count: int = 0):
    """
    rate  : transactions par seconde
    count : nombre total (0 = infini)
    """
    print(f"🚀 Starting Transaction Producer")
    print(f"   Broker: {KAFKA_BROKER}")
    print(f"   Topic:  {TOPIC}")
    print(f"   Rate:   {rate} tx/s")
    print(f"   Count:  {'∞' if count == 0 else count}")

    # Retry until Kafka is ready
    producer = None
    for attempt in range(30):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8"),
            )
            print(f"✅ Connected to Kafka on attempt {attempt+1}")
            break
        except Exception as e:
            print(f"⏳ Waiting for Kafka... attempt {attempt+1}/30 ({e})")
            time.sleep(5)
    if producer is None:
        raise Exception("❌ Could not connect to Kafka after 30 attempts")

    weights  = [p["weight"] for p in FRAUD_PATTERNS]
    sent     = 0
    interval = 1.0 / rate

    try:
        while True:
            pattern = random.choices(FRAUD_PATTERNS, weights=weights, k=1)[0]
            tx      = generate_transaction(pattern)

            producer.send(
                TOPIC,
                key=tx["tx_id"],
                value=tx)

            sent += 1
            icon = {"normal":"🟢","fraud_obvious":"🔴","fraud_subtle":"🟡"}[pattern["name"]]
            print(f"{icon} [{sent}] {tx['tx_id']} | "
                  f"{tx['montant_mad']:>8.2f} MAD | "
                  f"Pattern: {pattern['name']}")

            if count > 0 and sent >= count:
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n⏹️  Stopped after {sent} transactions")
    finally:
        producer.flush()
        producer.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate",  type=float, default=1.0,
                        help="Transactions per second")
    parser.add_argument("--count", type=int,   default=0,
                        help="Total count (0=infinite)")
    args = parser.parse_args()
    main(args.rate, args.count)
