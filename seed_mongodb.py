"""
Seed MongoDB with StratoTwin topology across all six layers.
Run this AFTER docker compose is up and PostgreSQL schema is initialized.
"""

from datetime import datetime, timezone
import random
import sys
from typing import Dict, List, Tuple

from pymongo import MongoClient, UpdateOne

MONGO_URI = "mongodb://localhost:27017"
SITES = ["CHN", "PUN", "MUM", "BLR", "NJ"]

LAYER_COMPONENTS: Dict[str, List[Tuple[str, str, str, float]]] = {
    "L1": [
        ("CR", "core-router", "Cisco IOS-XE", 0.30),
        ("FW", "firewall", "PAN-OS", 0.25),
        ("LB", "load-balancer", "F5 BIG-IP", 0.20),
        ("DS", "distribution-switch", "Cisco Catalyst", 0.10),
        ("AS", "access-switch", "Cisco Catalyst 9300", 0.05),
        ("AP", "wireless-ap", "Cisco Aironet", 0.05),
        ("DNS", "dns-server", "BIND 9", 0.05),
    ],
    "L2": [
        ("SRV", "physical-server", "Dell PowerEdge", 0.28),
        ("VM", "virtual-machine", "VMware", 0.18),
        ("POD", "k8s-pod", "Kubernetes", 0.18),
        ("K8S", "k8s-node", "Kubernetes", 0.16),
        ("GPU", "gpu-instance", "NVIDIA", 0.10),
        ("EDGE", "edge-node", "Linux Edge", 0.10),
    ],
    "L3": [
        ("GW", "api-gateway", "Kong", 0.25),
        ("AUTH", "auth-service", "Python/FastAPI", 0.20),
        ("ORDER", "order-service", "Java/Spring", 0.20),
        ("NOTIFY", "notification-service", "Node.js", 0.15),
        ("REPORT", "reporting-service", "Python", 0.20),
    ],
    "L4": [
        ("KFK", "kafka-topic", "Apache Kafka", 0.24),
        ("ETL", "etl-pipeline", "Spark", 0.22),
        ("VAULT", "compliance-vault", "Vault", 0.20),
        ("WH", "warehouse-table", "PostgreSQL", 0.17),
        ("FS", "feature-store", "Feast", 0.17),
    ],
    "L5": [
        ("EMP", "employee-node", "HRIS", 0.30),
        ("SKILL", "skill-node", "SkillGraph", 0.15),
        ("PROJ", "project-node", "PM Tool", 0.20),
        ("TEAM", "team-node", "OrgGraph", 0.20),
        ("CERT", "certification-node", "LMS", 0.15),
    ],
    "L6": [
        ("RACK", "server-rack", "Schneider", 0.30),
        ("UPS", "ups-unit", "APC", 0.25),
        ("CRAC", "cooling-unit", "Vertiv", 0.20),
        ("BMS", "bms-controller", "Honeywell", 0.15),
        ("PDU", "pdu-unit", "APC", 0.10),
    ],
}

L1_THRESHOLD_MAP = {
    "core-router": {"cpu_warn": 70, "cpu_crit": 90, "bw_warn": 75, "bw_crit": 90},
    "firewall": {"cpu_warn": 75, "cpu_crit": 92, "session_warn": 700000, "session_crit": 950000},
    "load-balancer": {"cpu_warn": 70, "cpu_crit": 85, "conn_warn": 70000, "conn_crit": 95000},
    "distribution-switch": {"cpu_warn": 70, "cpu_crit": 85, "bw_warn": 80, "bw_crit": 95},
    "access-switch": {"cpu_warn": 75, "cpu_crit": 90, "port_warn": 80, "port_crit": 95},
    "wireless-ap": {"cpu_warn": 70, "cpu_crit": 85, "client_warn": 50, "client_crit": 80},
    "dns-server": {"cpu_warn": 70, "cpu_crit": 85, "qps_warn": 10000, "qps_crit": 20000},
}


def utc_now():
    return datetime.now(timezone.utc)


def make_state(layer: str, node_type: str):
    if layer == "L1":
        base = {
            "cpu_util": round(random.uniform(10, 55), 1),
            "bw_util": round(random.uniform(15, 60), 1),
            "latency_ms": round(random.uniform(0.3, 2.5), 2),
            "status": "ok",
            "health": "ok",
        }
        if node_type == "firewall":
            base["session_count"] = random.randint(100000, 500000)
        if node_type == "load-balancer":
            base["active_conn"] = random.randint(5000, 50000)
        if node_type == "dns-server":
            base["queries_per_sec"] = random.randint(500, 8000)
        return base

    if layer == "L2":
        return {
            "cpu_util": round(random.uniform(18, 88), 1),
            "memory_util": round(random.uniform(20, 92), 1),
            "disk_util": round(random.uniform(15, 80), 1),
            "status": "ok",
        }
    if layer == "L3":
        return {
            "rps": random.randint(100, 4500),
            "error_rate": round(random.uniform(0.001, 0.08), 3),
            "p95_latency_ms": round(random.uniform(12, 550), 1),
            "status": "ok",
        }
    if layer == "L4":
        return {
            "consumer_lag": random.randint(0, 12000),
            "etl_duration_sec": round(random.uniform(15, 400), 1),
            "throughput_rpm": random.randint(1000, 100000),
            "status": "ok",
        }
    if layer == "L5":
        return {
            "active_staff": random.randint(30, 350),
            "bench_duration_days": random.randint(0, 70),
            "attrition_risk_score": round(random.uniform(0.05, 0.55), 3),
            "status": "ok",
        }
    return {
        "rack_temp_celsius": round(random.uniform(22, 31), 1),
        "ups_battery_pct": round(random.uniform(45, 100), 1),
        "cooling_status": "ok",
        "status": "ok",
    }


def health_score_for(layer: str, node_type: str, state: Dict):
    if layer == "L1":
        thresholds = L1_THRESHOLD_MAP.get(node_type, {})
        cpu = float(state.get("cpu_util", 0))
        health_score = 100.0
        if cpu > thresholds.get("cpu_crit", 999):
            health_score -= 35
        elif cpu > thresholds.get("cpu_warn", 999):
            health_score -= 15
        if state.get("status") == "down":
            health_score = 0
        return round(max(0, health_score), 1)
    return round(random.uniform(72, 98), 1)


def node_id_for(layer: str, site: str, short: str):
    if layer == "L5" and short == "EMP":
        return f"{layer}-{site}-{short}-1042"
    return f"{layer}-{site}-{short}-01"


def display_name(site: str, node_type: str):
    return f"{site} {node_type.replace('-', ' ').title()} 01"


def seed_mongodb():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client["stratotwin"]
        db.command("ping")
        print("[SUCCESS] Connected to MongoDB")
    except Exception as e:
        print(f"[ERROR] Cannot connect to MongoDB at {MONGO_URI}")
        print(f"   Error: {e}")
        print("   Make sure: docker compose up -d")
        sys.exit(1)

    print("\n[1/5] Seeding node_registry + component_twins...")
    nodes = []
    component_twins = []
    asset_twins_map: Dict[str, List[str]] = {}
    asset_weight_map: Dict[str, Dict[str, float]] = {}

    for layer, defs in LAYER_COMPONENTS.items():
        for site in SITES:
            asset_id = f"ASSET-{layer}-{site}"
            asset_nodes: List[str] = []
            weights: Dict[str, float] = {}

            for (short, node_type, vendor, weight) in defs:
                node_id = node_id_for(layer, site, short)
                asset_nodes.append(node_id)
                weights[node_id] = weight

                state = make_state(layer, node_type)
                health_score = health_score_for(layer, node_type, state)
                ts = utc_now()
                node_doc = {
                    "node_id": node_id,
                    "layer": layer,
                    "site": site,
                    "type": node_type,
                    "instance": "01",
                    "display_name": display_name(site, node_type),
                    "topology_version": 1,
                    "created_at": ts,
                    "updated_at": ts,
                    "config": {
                        "vendor": vendor,
                        "thresholds": L1_THRESHOLD_MAP.get(node_type, {}),
                    },
                }
                twin_doc = {
                    "node_id": node_id,
                    "layer": layer,
                    "site": site,
                    "type": node_type,
                    "display_name": node_doc["display_name"],
                    "topology_version": 1,
                    "config": {"vendor": vendor, "thresholds": L1_THRESHOLD_MAP.get(node_type, {})},
                    "state": state,
                    "health_score": health_score,
                    "last_updated": ts,
                    "active_alerts": [],
                }
                nodes.append(node_doc)
                component_twins.append(twin_doc)

            asset_twins_map[asset_id] = asset_nodes
            asset_weight_map[asset_id] = weights

    db.node_registry.bulk_write(
        [UpdateOne({"node_id": n["node_id"]}, {"$set": n}, upsert=True) for n in nodes]
    )
    db.component_twins.bulk_write(
        [UpdateOne({"node_id": t["node_id"]}, {"$set": t}, upsert=True) for t in component_twins]
    )
    db.node_registry.create_index([("node_id", 1)], unique=True)
    db.node_registry.create_index([("layer", 1), ("site", 1)])
    db.component_twins.create_index([("node_id", 1)], unique=True)
    db.component_twins.create_index([("layer", 1), ("site", 1)])
    db.component_twins.create_index([("last_updated", -1)])
    print(f"   [OK] Seeded {len(nodes)} nodes in node_registry")
    print(f"   [OK] Seeded {len(component_twins)} component_twins")

    print("[2/5] Seeding asset_twins...")
    ops_at = []
    for asset_id, component_ids in asset_twins_map.items():
        layer = asset_id.split("-")[1]
        site = asset_id.split("-")[2]
        weights = asset_weight_map[asset_id]
        agg_health = 0.0
        for nid in component_ids:
            twin = next((t for t in component_twins if t["node_id"] == nid), None)
            if twin:
                agg_health += float(twin["health_score"]) * float(weights[nid])
        doc = {
            "asset_id": asset_id,
            "layer": layer,
            "site": site,
            "display_name": f"{site} {layer} Asset",
            "topology_version": 1,
            "component_node_ids": component_ids,
            "health_weights": weights,
            "aggregated_health_score": round(agg_health, 1),
            "health_aggregation_method": "weighted_average",
            "active_alerts": [],
            "last_updated": utc_now(),
        }
        ops_at.append(UpdateOne({"asset_id": asset_id}, {"$set": doc}, upsert=True))

    db.asset_twins.bulk_write(ops_at)
    db.asset_twins.create_index([("asset_id", 1)], unique=True)
    db.asset_twins.create_index([("layer", 1), ("site", 1)])
    print(f"   [OK] Seeded {len(ops_at)} asset_twins")

    print("[3/5] Seeding system_twin...")
    layer_scores = {}
    for layer in LAYER_COMPONENTS.keys():
        rows = list(db.asset_twins.find({"layer": layer}, {"aggregated_health_score": 1}))
        avg = sum(r["aggregated_health_score"] for r in rows) / max(len(rows), 1)
        layer_scores[layer] = round(avg, 1)

    layer_weights = {"L1": 0.25, "L2": 0.20, "L3": 0.20, "L4": 0.15, "L5": 0.10, "L6": 0.10}
    system_health = sum(layer_scores[l] * layer_weights[l] for l in layer_scores)
    system_doc = {
        "system_id": "STRATOTWIN-ENTERPRISE-V1",
        "topology_version": 1,
        "created_at": utc_now(),
        "asset_ids": list(asset_twins_map.keys()),
        "system_health_score": round(system_health, 1),
        "layer_health_scores": layer_scores,
        "layer_weights": layer_weights,
        "last_snapshot_at": utc_now(),
        "snapshot_interval_seconds": 300,
    }
    db.system_twin.update_one({"system_id": "STRATOTWIN-ENTERPRISE-V1"}, {"$set": system_doc}, upsert=True)
    print(f"   [OK] Seeded system_twin (health={system_health:.1f})")

    print("[4/5] Seeding wan_links...")
    wan_links = [
        {"link_id": "WAN-CHN-PUN-01", "src": "L1-CHN-CR-01", "dst": "L1-PUN-CR-01", "type": "MPLS", "bw": 1000, "lat_sla": 10, "latency": 10.2},
        {"link_id": "WAN-CHN-MUM-01", "src": "L1-CHN-CR-01", "dst": "L1-MUM-CR-01", "type": "MPLS", "bw": 500, "lat_sla": 8, "latency": 8.1},
        {"link_id": "WAN-CHN-BLR-01", "src": "L1-CHN-CR-01", "dst": "L1-BLR-CR-01", "type": "MPLS", "bw": 500, "lat_sla": 6, "latency": 5.9},
        {"link_id": "WAN-PUN-MUM-01", "src": "L1-PUN-CR-01", "dst": "L1-MUM-CR-01", "type": "SD-WAN", "bw": 200, "lat_sla": 12, "latency": 11.5},
        {"link_id": "WAN-PUN-NJ-01", "src": "L1-PUN-CR-01", "dst": "L1-NJ-CR-01", "type": "MPLS", "bw": 100, "lat_sla": 190, "latency": 188.4},
        {"link_id": "WAN-MUM-NJ-01", "src": "L1-MUM-CR-01", "dst": "L1-NJ-CR-01", "type": "Internet", "bw": 50, "lat_sla": 200, "latency": 198.7},
    ]
    ops_wan = []
    for link in wan_links:
        util = round(random.uniform(15, 65), 1)
        doc = {
            "link_id": link["link_id"],
            "source_node": link["src"],
            "target_node": link["dst"],
            "type": link["type"],
            "topology_version": 1,
            "config": {
                "bandwidth_mbps": link["bw"],
                "committed_rate_mbps": int(link["bw"] * 0.7),
                "sla": {"latency_ms": link["lat_sla"], "jitter_ms": 5, "packet_loss_pct": 0.1},
            },
            "state": {
                "utilization_pct": util,
                "latency_ms": link["latency"] + round(random.uniform(-0.5, 0.5), 2),
                "jitter_ms": round(random.uniform(0.2, 1.5), 2),
                "packet_loss_pct": 0.0,
                "status": "ok",
            },
            "thresholds": {"util_warn": 75, "util_crit": 90, "latency_breach_multiplier": 1.5},
            "last_updated": utc_now(),
        }
        ops_wan.append(UpdateOne({"link_id": link["link_id"]}, {"$set": doc}, upsert=True))
    db.wan_links.bulk_write(ops_wan)
    db.wan_links.create_index([("link_id", 1)], unique=True)
    print(f"   [OK] Seeded {len(ops_wan)} wan_links")

    print("[5/5] Ensuring process collections...")
    for name in ["process_definitions", "process_executions", "incidents", "simulation_runs"]:
        db[name].create_index([("created_at", -1)])
    print("   [OK] Process collections ready")

    print("\n[SUCCESS] All MongoDB seeds complete!")
    print(
        "   Totals: "
        f"{db.node_registry.count_documents({})} nodes, "
        f"{db.asset_twins.count_documents({})} assets, "
        f"{db.system_twin.count_documents({})} system, "
        f"{db.wan_links.count_documents({})} WAN links"
    )


if __name__ == "__main__":
    seed_mongodb()

