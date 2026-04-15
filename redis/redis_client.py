import os
import redis
import json
import time
import hashlib
from datetime import datetime
from typing import Optional, Dict

class FraudRedisClient:
    def __init__(self, host=None, port=6379, db=0):
        # Support Docker : REDIS_HOST env var
        redis_host = host or os.getenv("REDIS_HOST", "localhost")
        self.client = redis.Redis(
            host=redis_host, port=port, db=db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        self.client.ping()
        print(f"✅ Redis connecté sur {redis_host}:{port}")

    def is_already_processed(self, tx_id: str) -> bool:
        return self.client.exists(f"tx:{tx_id}:processed") > 0

    def mark_as_processed(self, tx_id: str, result: Dict, ttl: int = 86400):
        self.client.setex(f"tx:{tx_id}:processed", ttl, json.dumps(result))

    def get_cached_decision(self, tx_id: str) -> Optional[Dict]:
        data = self.client.get(f"decision:{tx_id}")
        return json.loads(data) if data else None

    def cache_decision(self, tx_id: str, decision: Dict, ttl: int = 3600):
        self.client.setex(f"decision:{tx_id}", ttl, json.dumps(decision))
        self.client.lpush("decisions:recent", tx_id)
        self.client.ltrim("decisions:recent", 0, 999)

    def get_recent_decisions(self, limit: int = 50) -> list:
        return self.client.lrange("decisions:recent", 0, limit - 1)

    def push_to_outbox(self, event_type: str, payload: Dict) -> str:
        event_id = hashlib.sha256(
            f"{payload.get('tx_id','')}{time.time()}".encode()
        ).hexdigest()[:16]
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "payload": payload,
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0,
            "status": "PENDING"
        }
        self.client.lpush("outbox:pending", json.dumps(event))
        self.client.setex(f"outbox:event:{event_id}", 3600, json.dumps(event))
        return event_id

    def pop_from_outbox(self, timeout: int = 1) -> Optional[Dict]:
        result = self.client.brpop("outbox:pending", timeout=timeout)
        if result:
            _, data = result
            return json.loads(data)
        return None

    def mark_outbox_success(self, event_id: str, event_data: Dict):
        event_data["status"] = "SUCCESS"
        event_data["processed_at"] = datetime.utcnow().isoformat()
        self.client.setex(f"outbox:event:{event_id}", 3600, json.dumps(event_data))
        self.client.incr("outbox:stats:success")

    def mark_outbox_failed(self, event_id: str, error: str, event_data: Dict):
        event_data["attempts"] = event_data.get("attempts", 0) + 1
        event_data["last_error"] = error
        event_data["status"] = "FAILED"
        if event_data["attempts"] < 3:
            self.client.lpush("outbox:pending", json.dumps(event_data))
        else:
            self.client.lpush("outbox:dead_letter", json.dumps(event_data))
            self.client.incr("outbox:stats:dead_letter")
        self.client.incr("outbox:stats:failed")

    def get_outbox_stats(self) -> Dict:
        return {
            "pending": self.client.llen("outbox:pending"),
            "dead_letter": self.client.llen("outbox:dead_letter"),
            "total_success": int(self.client.get("outbox:stats:success") or 0),
            "total_failed": int(self.client.get("outbox:stats:failed") or 0),
        }

    def check_card_rate_limit(self, card_id: str, window_seconds: int = 600, max_transactions: int = 5) -> Dict:
        key = f"rate:{card_id}:{window_seconds}s"
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        count, _ = pipe.execute()
        exceeded = count > max_transactions
        if exceeded:
            alert = {
                "card_id": card_id, "count": count,
                "window": window_seconds,
                "detected_at": datetime.utcnow().isoformat(),
                "alert_type": "RATE_LIMIT_EXCEEDED"
            }
            self.client.lpush("alerts:rate_limit", json.dumps(alert))
            self.client.ltrim("alerts:rate_limit", 0, 499)
        return {"exceeded": exceeded, "count": count, "max": max_transactions, "window_seconds": window_seconds}

    def check_client_velocity(self, client_id: str, amount: float, window_seconds: int = 3600) -> Dict:
        key_count = f"velocity:{client_id}:count:{window_seconds}s"
        key_amount = f"velocity:{client_id}:amount:{window_seconds}s"
        pipe = self.client.pipeline()
        pipe.incr(key_count)
        pipe.expire(key_count, window_seconds)
        pipe.incrbyfloat(key_amount, amount)
        pipe.expire(key_amount, window_seconds)
        results = pipe.execute()
        total_count = int(results[0])
        total_amount = float(results[2])
        suspicious = total_count > 10 or total_amount > 50000
        return {"suspicious": suspicious, "total_transactions": total_count, "total_amount": total_amount}

    def set_card_block_status(self, card_id: str, status: Dict, ttl: int = 300):
        self.client.setex(f"card:{card_id}:status", ttl, json.dumps(status))

    def get_card_block_status(self, card_id: str) -> Optional[Dict]:
        data = self.client.get(f"card:{card_id}:status")
        return json.loads(data) if data else None

    def increment_zone_counter(self, zone: str):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        self.client.incr(f"stats:{today}:zone:{zone}")
        self.client.incr(f"stats:total:zone:{zone}")
        self.client.expire(f"stats:{today}:zone:{zone}", 86400 * 7)

    def get_today_stats(self) -> Dict:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return {
            "FRAUDE": int(self.client.get(f"stats:{today}:zone:FRAUDE") or 0),
            "AMBIGU": int(self.client.get(f"stats:{today}:zone:AMBIGU") or 0),
            "LEGITIME": int(self.client.get(f"stats:{today}:zone:LEGITIME") or 0),
            "outbox": self.get_outbox_stats()
        }

    def get_alerts(self, limit: int = 20) -> list:
        alerts = self.client.lrange("alerts:rate_limit", 0, limit - 1)
        return [json.loads(a) for a in alerts]
