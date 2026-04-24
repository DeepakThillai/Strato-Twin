"""
Phase 2 verification:
- Kafka topics visible
- Process definitions seeded
- Process executions generated
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from kafka import KafkaAdminClient
from pymongo import MongoClient

KAFKA_BOOTSTRAP = "127.0.0.1:9092"
MONGO_URI = "mongodb://localhost:27017"
REQUIRED_TOPICS = {
    "network.node.state",
    "compute.node.state",
    "application.service.state",
    "data.pipeline.state",
    "workforce.state",
    "facilities.sensor.state",
    "stratotwin.alerts",
}


def main() -> int:
    print("=" * 60)
    print("StratoTwin Phase 2 Verification")
    print("=" * 60)

    admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP, request_timeout_ms=5000)
    topics = set(admin.list_topics())
    admin.close()
    missing = REQUIRED_TOPICS - topics
    print(f"[Kafka] topics visible={len(topics)}")
    if missing:
        print(f"[Kafka] missing required topics: {sorted(missing)}")
        return 1

    mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = mongo["stratotwin"]
    db.command("ping")

    defs_count = db.process_definitions.count_documents({})
    print(f"[Mongo] process_definitions={defs_count}")
    if defs_count < 13:
        print("[Mongo] process definitions not fully seeded")
        return 1

    since = datetime.now(timezone.utc) - timedelta(minutes=5)
    exe_count = db.process_executions.count_documents({"created_at": {"$gte": since}})
    print(f"[Mongo] process_executions (last 5m)={exe_count}")
    if exe_count == 0:
        print("[Mongo] no recent process executions found")
        return 1

    alerts_count = db["process_executions"].count_documents({"indicator": {"$in": ["negative", "attack"]}})
    print(f"[Mongo] non-positive executions={alerts_count}")

    print("\n[SUCCESS] PHASE 2 PIPELINE IS RUNNING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

