"""
StratoTwin Phase 2 base simulator.
Publishes synthetic layer metrics to Kafka.
"""
from __future__ import annotations

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from kafka import KafkaProducer

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP", "127.0.0.1:9092")
SITES = ["CHN", "PUN", "MUM", "BLR", "NJ"]

TOPIC_BY_LAYER = {
    "L1": "network.node.state",
    "L2": "compute.node.state",
    "L3": "application.service.state",
    "L4": "data.pipeline.state",
    "L5": "workforce.state",
    "L6": "facilities.sensor.state",
}

DEFAULT_INTERVAL_BY_LAYER = {
    "L1": 5,
    "L2": 8,
    "L3": 8,
    "L4": 12,
    "L5": 20,
    "L6": 15,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _network_nodes() -> List[Dict[str, str]]:
    types = ["CR", "FW", "LB", "DS", "AS", "AP", "DNS"]
    nodes: List[Dict[str, str]] = []
    for site in SITES:
        for short in types:
            nodes.append({"node_id": f"L1-{site}-{short}-01", "site": site, "layer": "L1"})
    return nodes


def _generic_nodes(layer: str, entity: str, count_per_site: int) -> List[Dict[str, str]]:
    nodes: List[Dict[str, str]] = []
    for site in SITES:
        for i in range(1, count_per_site + 1):
            nodes.append({"node_id": f"{layer}-{site}-{entity}-{i:02d}", "site": site, "layer": layer})
    return nodes


NODES_BY_LAYER = {
    "L1": _network_nodes(),
    "L2": _generic_nodes("L2", "NODE", 4),
    "L3": _generic_nodes("L3", "SVC", 4),
    "L4": _generic_nodes("L4", "PIPE", 3),
    "L5": _generic_nodes("L5", "TEAM", 2),
    "L6": _generic_nodes("L6", "RACK", 2),
}


def _metrics_for_layer(layer: str) -> Dict[str, float]:
    if layer == "L1":
        return {
            "cpu_util": round(random.uniform(10, 90), 1),
            "bw_util": round(random.uniform(10, 95), 1),
            "latency_ms": round(random.uniform(1, 25), 2),
            "syn_rate": random.randint(100, 9000),
            "packet_drop_rate": round(random.uniform(0.0, 0.12), 4),
        }
    if layer == "L2":
        return {
            "cpu_util": round(random.uniform(15, 98), 1),
            "memory_util": round(random.uniform(20, 98), 1),
            "pod_restart_count": random.randint(0, 10),
            "syscall_anomaly_score": round(random.uniform(0.0, 1.0), 3),
        }
    if layer == "L3":
        return {
            "rps": random.randint(50, 6000),
            "error_rate": round(random.uniform(0.0, 0.25), 3),
            "p95_latency_ms": round(random.uniform(10, 1200), 1),
            "source_ip_count": random.randint(5, 10000),
        }
    if layer == "L4":
        return {
            "records_per_minute": random.randint(100, 150000),
            "consumer_lag": random.randint(0, 200000),
            "etl_duration_sec": round(random.uniform(10, 1200), 1),
            "schema_change_events": random.randint(0, 5),
        }
    if layer == "L5":
        return {
            "active_staff": random.randint(20, 400),
            "bench_duration_days": random.randint(0, 180),
            "attrition_risk_score": round(random.uniform(0.0, 1.0), 3),
            "access_attempts": random.randint(1, 500),
        }
    return {
        "rack_temp_celsius": round(random.uniform(22, 43), 1),
        "ups_battery_pct": round(random.uniform(20, 100), 1),
        "cooling_status": random.randint(0, 1),
        "badge_anomaly_score": round(random.uniform(0.0, 1.0), 3),
    }


def run_layer_simulator(layer: str) -> None:
    if layer not in TOPIC_BY_LAYER:
        raise ValueError(f"Unsupported layer: {layer}")

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda v: v.encode("utf-8"),
        linger_ms=50,
    )
    topic = TOPIC_BY_LAYER[layer]
    interval = float(os.getenv("SIM_INTERVAL_SEC", DEFAULT_INTERVAL_BY_LAYER[layer]))
    nodes = NODES_BY_LAYER[layer]
    sent = 0

    print(f"[START] {layer} simulator -> topic={topic}, interval={interval}s, nodes={len(nodes)}")

    while True:
        node = random.choice(nodes)
        payload = {
            "event_id": f"evt-{uuid.uuid4()}",
            "timestamp": _now_iso(),
            "source": "phase2-simulator",
            "layer": layer,
            "site": node["site"],
            "node_id": node["node_id"],
            "status": "ok",
            "metrics": _metrics_for_layer(layer),
        }
        producer.send(topic, key=node["node_id"], value=payload)
        sent += 1
        if sent % 20 == 0:
            producer.flush()
            print(f"[INFO] {layer} sent={sent}")
        time.sleep(interval)

