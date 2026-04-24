"""
StratoTwin Phase 2 process engine.
Consumes simulator events, persists process executions, emits alerts.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from kafka import KafkaConsumer, KafkaProducer
from pymongo import MongoClient, UpdateOne

KAFKA_BOOTSTRAP = "127.0.0.1:9092"
MONGO_URI = "mongodb://localhost:27017"

TOPICS = [
    "network.node.state",
    "compute.node.state",
    "application.service.state",
    "data.pipeline.state",
    "workforce.state",
    "facilities.sensor.state",
]

PROCESS_BY_LAYER = {
    "L1": "PROC-L1L3-002",
    "L2": "PROC-L2L3-006",
    "L3": "PROC-L2L3-007",
    "L4": "PROC-L3L4-009",
    "L5": "PROC-L5-011",
    "L6": "PROC-L6L2-012",
}

PROCESS_DEFINITIONS = [
    {"process_id": "PROC-L1L2L3-001", "name": "Internal app access", "layers": ["L1", "L2", "L3"]},
    {"process_id": "PROC-L1L3-002", "name": "Internet-bound traffic", "layers": ["L1", "L3"]},
    {"process_id": "PROC-L1-003", "name": "WAN site-to-site", "layers": ["L1"]},
    {"process_id": "PROC-L1-004", "name": "BGP flap and convergence", "layers": ["L1"]},
    {"process_id": "PROC-L1L5-005", "name": "802.1X device auth", "layers": ["L1", "L5"]},
    {"process_id": "PROC-L2L3-006", "name": "Container scheduling", "layers": ["L2", "L3"]},
    {"process_id": "PROC-L2L3-007", "name": "Microservice API chain", "layers": ["L2", "L3"]},
    {"process_id": "PROC-L2L3-008", "name": "CI/CD pipeline", "layers": ["L2", "L3"]},
    {"process_id": "PROC-L3L4-009", "name": "Data pipeline ingestion", "layers": ["L3", "L4"]},
    {"process_id": "PROC-L4L5-010", "name": "Data lineage and compliance", "layers": ["L4", "L5"]},
    {"process_id": "PROC-L5-011", "name": "Workforce skill matching", "layers": ["L5"]},
    {"process_id": "PROC-L6L2-012", "name": "Facilities power/cooling", "layers": ["L6", "L2"]},
    {"process_id": "PROC-ALL-013", "name": "Cross-layer propagation", "layers": ["L1", "L2", "L3", "L4", "L5", "L6"]},
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def evaluate_indicator(layer: str, metrics: Dict[str, Any]) -> str:
    if layer == "L1":
        if metrics.get("syn_rate", 0) > 7000 or metrics.get("packet_drop_rate", 0.0) > 0.08:
            return "attack"
        if metrics.get("cpu_util", 0.0) > 90 or metrics.get("bw_util", 0.0) > 90:
            return "negative"
    elif layer == "L2":
        if metrics.get("syscall_anomaly_score", 0.0) > 0.9:
            return "attack"
        if metrics.get("cpu_util", 0.0) > 95 or metrics.get("memory_util", 0.0) > 95:
            return "negative"
    elif layer == "L3":
        if metrics.get("source_ip_count", 0) > 8000 and metrics.get("error_rate", 0.0) > 0.12:
            return "attack"
        if metrics.get("error_rate", 0.0) > 0.1 or metrics.get("p95_latency_ms", 0.0) > 900:
            return "negative"
    elif layer == "L4":
        if metrics.get("consumer_lag", 0) > 100000:
            return "negative"
    elif layer == "L5":
        if metrics.get("attrition_risk_score", 0.0) > 0.9:
            return "attack"
        if metrics.get("bench_duration_days", 0) > 120:
            return "negative"
    elif layer == "L6":
        if metrics.get("badge_anomaly_score", 0.0) > 0.95:
            return "attack"
        if metrics.get("rack_temp_celsius", 0.0) > 36:
            return "negative"
    return "positive"


def severity_for_indicator(indicator: str) -> str:
    if indicator == "attack":
        return "critical"
    if indicator == "negative":
        return "high"
    return "info"


def build_execution(event: Dict[str, Any]) -> Dict[str, Any]:
    layer = event.get("layer", "L1")
    metrics = event.get("metrics", {})
    indicator = evaluate_indicator(layer, metrics)
    process_id = PROCESS_BY_LAYER.get(layer, "PROC-ALL-013")
    now = utc_now()
    return {
        "execution_id": f"exec-{uuid.uuid4()}",
        "process_id": process_id,
        "trigger_event_id": event.get("event_id"),
        "layer": layer,
        "site": event.get("site"),
        "node_id": event.get("node_id"),
        "started_at": now,
        "ended_at": now,
        "status": "completed" if indicator == "positive" else "degraded",
        "indicator": indicator,
        "metrics_snapshot": metrics,
        "steps": [
            {
                "step": "ingest_event",
                "ts": now,
                "ok": True,
                "notes": f"topic={event.get('topic', 'unknown')}",
            },
            {
                "step": "evaluate_indicator",
                "ts": now,
                "ok": True,
                "notes": f"indicator={indicator}",
            },
        ],
        "created_at": now,
    }


def upsert_process_definitions(db) -> None:
    ops: List[UpdateOne] = []
    now = utc_now()
    for item in PROCESS_DEFINITIONS:
        doc = {
            "process_id": item["process_id"],
            "name": item["name"],
            "layers": item["layers"],
            "version": 1,
            "active": True,
            "updated_at": now,
        }
        ops.append(UpdateOne({"process_id": item["process_id"]}, {"$set": doc}, upsert=True))
    if ops:
        db.process_definitions.bulk_write(ops)
    db.process_definitions.create_index([("process_id", 1)], unique=True)
    db.process_executions.create_index([("execution_id", 1)], unique=True)
    db.process_executions.create_index([("created_at", -1)])
    db.incidents.create_index([("created_at", -1)])


def emit_alert(producer: KafkaProducer, execution: Dict[str, Any]) -> None:
    indicator = execution["indicator"]
    if indicator == "positive":
        return
    payload = {
        "alert_id": f"alert-{uuid.uuid4()}",
        "timestamp": utc_now().isoformat(),
        "severity": severity_for_indicator(indicator),
        "indicator": indicator,
        "process_id": execution["process_id"],
        "node_id": execution["node_id"],
        "layer": execution["layer"],
        "site": execution["site"],
        "message": f"{indicator.upper()} detected for {execution['node_id']}",
    }
    producer.send("stratotwin.alerts", value=payload, key=execution["node_id"].encode("utf-8"))


def run() -> None:
    mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = mongo["stratotwin"]
    db.command("ping")
    upsert_process_definitions(db)

    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset="latest",
        group_id="stratotwin-process-engine-v1",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print("[START] Process engine consuming phase2 topics...")
    processed = 0

    for msg in consumer:
        event = msg.value
        event["topic"] = msg.topic
        execution = build_execution(event)
        db.process_executions.insert_one(execution)
        emit_alert(producer, execution)
        processed += 1
        if processed % 25 == 0:
            producer.flush()
            print(f"[INFO] processed={processed}")


if __name__ == "__main__":
    run()

