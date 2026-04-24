"""
StratoTwin Tool API (Phase 3).
"""
from __future__ import annotations

import asyncio
import json
import re
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List

import psycopg2
import redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
PG_CONFIG = {
    "host": "127.0.0.1",
    "port": 55432,
    "database": "stratotwin",
    "user": "stratotwin",
    "password": "stratotwin_pass",
}
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379

app = FastAPI(title="StratoTwin Tool API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_mongo():
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)["stratotwin"]


def get_pg_conn():
    return psycopg2.connect(**PG_CONFIG)


def get_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def compute_blast_radius(start_node_id: str) -> Dict[str, Any]:
    cache = get_redis()
    key = f"blast_radius:{start_node_id}"
    cached = cache.get(key)
    if cached:
        return json.loads(cached)

    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source_node_id, source_layer, target_node_id, target_layer, relationship
        FROM cross_layer_dependencies
        """
    )
    edges = cur.fetchall()
    cur.close()
    conn.close()

    graph: Dict[str, List[Dict[str, str]]] = {}
    for src, src_layer, dst, dst_layer, rel in edges:
        graph.setdefault(src, []).append(
            {
                "target_node_id": dst,
                "source_layer": src_layer,
                "target_layer": dst_layer,
                "relationship": rel,
            }
        )

    visited = {start_node_id}
    q = deque([start_node_id])
    impacted_nodes: List[Dict[str, str]] = []
    relationships: List[Dict[str, str]] = []

    while q:
        cur_node = q.popleft()
        for edge in graph.get(cur_node, []):
            nxt = edge["target_node_id"]
            relationships.append({"source_node_id": cur_node, **edge})
            if nxt not in visited:
                visited.add(nxt)
                impacted_nodes.append(
                    {"node_id": nxt, "layer": edge["target_layer"], "relationship": edge["relationship"]}
                )
                q.append(nxt)

    result = {
        "start_node_id": start_node_id,
        "impacted_count": len(impacted_nodes),
        "impacted_nodes": impacted_nodes,
        "relationships": relationships,
    }
    cache.setex(key, 30, json.dumps(result))
    return result


def _json_ready_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, list):
        return [_json_ready_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _json_ready_value(v) for k, v in value.items()}
    return value


def _json_ready_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(doc)
    if "_id" in out:
        out["_id"] = str(out["_id"])
    return {k: _json_ready_value(v) for k, v in out.items()}


class QueryRequest(BaseModel):
    question: str


@app.get("/health")
def health() -> Dict[str, Any]:
    status = {"status": "ok"}
    db = get_mongo()
    db.command("ping")
    status["mongo"] = "ok"

    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    cur.fetchone()
    cur.close()
    conn.close()
    status["postgres"] = "ok"

    cache = get_redis()
    cache.ping()
    status["redis"] = "ok"
    return status


@app.get("/topology")
def topology() -> Dict[str, Any]:
    db = get_mongo()
    return {
        "node_registry": db.node_registry.count_documents({}),
        "component_twins": db.component_twins.count_documents({}),
        "asset_twins": db.asset_twins.count_documents({}),
        "system_twin": db.system_twin.count_documents({}),
        "wan_links": db.wan_links.count_documents({}),
    }


@app.get("/topology/graph")
def topology_graph(limit_nodes: int = 300) -> Dict[str, Any]:
    db = get_mongo()
    nodes = list(
        db.component_twins.find(
            {},
            {
                "_id": 0,
                "node_id": 1,
                "layer": 1,
                "site": 1,
                "type": 1,
                "display_name": 1,
                "health_score": 1,
                "state.status": 1,
            },
        ).limit(limit_nodes)
    )
    edges = list(
        db.wan_links.find(
            {},
            {
                "_id": 0,
                "link_id": 1,
                "source_node": 1,
                "target_node": 1,
                "type": 1,
                "state.status": 1,
                "state.latency_ms": 1,
            },
        )
    )
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source_node_id, target_node_id, relationship
        FROM cross_layer_dependencies
        LIMIT 2000
        """
    )
    dep_rows = cur.fetchall()
    cur.close()
    conn.close()

    dep_edges = []
    for i, (src, dst, rel) in enumerate(dep_rows):
        dep_edges.append(
            {
                "link_id": f"DEP-{i+1}",
                "source_node": src,
                "target_node": dst,
                "type": rel,
                "state": {"status": "ok"},
            }
        )

    return {"nodes": nodes, "edges": edges + dep_edges}


@app.get("/alerts/recent")
def alerts_recent(limit: int = 20) -> Dict[str, Any]:
    db = get_mongo()
    docs = list(db.process_executions.find({"indicator": {"$in": ["negative", "attack"]}}).sort("created_at", -1).limit(limit))
    return {"count": len(docs), "alerts": [_json_ready_doc(d) for d in docs]}


@app.get("/blast-radius/{node_id}")
def blast_radius(node_id: str) -> Dict[str, Any]:
    return compute_blast_radius(node_id)


@app.post("/query")
def query(req: QueryRequest) -> Dict[str, Any]:
    text = (req.question or "").strip()
    lower = text.lower()

    if "blast" in lower and "radius" in lower:
        match = re.search(r"(L[1-6]-[A-Z]{3}-[A-Z0-9]+-\d{2,4})", text, flags=re.IGNORECASE)
        if not match:
            return {
                "intent": "blast_radius",
                "ok": False,
                "message": "Node id not found in question. Example: L6-CHN-RACK-01",
            }
        node_id = match.group(1).upper()
        return {"intent": "blast_radius", "ok": True, "result": compute_blast_radius(node_id)}

    if "topology" in lower or "summary" in lower:
        return {"intent": "topology_summary", "ok": True, "result": topology()}

    if "alert" in lower or "incident" in lower:
        limit = 20
        m = re.search(r"\b(\d{1,3})\b", lower)
        if m:
            limit = max(1, min(100, int(m.group(1))))
        return {"intent": "recent_alerts", "ok": True, "result": alerts_recent(limit=limit)}

    return {
        "intent": "unknown",
        "ok": False,
        "message": "Supported intents: blast radius, topology summary, alerts/incidents",
    }


@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket) -> None:
    await websocket.accept()
    db = get_mongo()
    last_seen = datetime.now(timezone.utc)
    try:
        while True:
            docs = list(
                db.process_executions.find(
                    {"indicator": {"$in": ["negative", "attack"]}, "created_at": {"$gt": last_seen}}
                )
                .sort("created_at", 1)
                .limit(100)
            )
            for d in docs:
                payload = _json_ready_doc(d)
                await websocket.send_text(json.dumps({"type": "alert", "payload": payload}))
                created_at = d.get("created_at")
                if isinstance(created_at, datetime) and created_at > last_seen:
                    last_seen = created_at
            await websocket.send_text(json.dumps({"type": "heartbeat"}))
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        return

