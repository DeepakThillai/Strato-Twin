"""
Common utilities for Phase 4 layer agents.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx
from pymongo import MongoClient

TOOL_API_BASE = "http://127.0.0.1:8080"
MONGO_URI = "mongodb://localhost:27017"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _severity_weight(indicator: str) -> int:
    if indicator == "attack":
        return 3
    if indicator == "negative":
        return 2
    return 1


class BaseLayerAgent:
    def __init__(self, name: str, focus_layer: str) -> None:
        self.name = name
        self.focus_layer = focus_layer

    def _blast_radius(self, node_id: str) -> Dict[str, Any]:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{TOOL_API_BASE}/blast-radius/{node_id}")
            resp.raise_for_status()
            return resp.json()

    def _node_recent_events(self, node_id: str, minutes: int = 30) -> List[Dict[str, Any]]:
        db = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)["stratotwin"]
        since = _utc_now() - timedelta(minutes=minutes)
        events = list(
            db.process_executions.find(
                {"node_id": node_id, "created_at": {"$gte": since}}
            )
            .sort("created_at", -1)
            .limit(30)
        )
        return events

    def _priority(self, alert_layer: str, indicator: str, impacted_count: int) -> str:
        score = _severity_weight(indicator)
        if alert_layer == self.focus_layer:
            score += 2
        if impacted_count >= 2:
            score += 1
        if score >= 5:
            return "critical"
        if score >= 3:
            return "high"
        return "medium"

    def analyze(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        node_id = alert["node_id"]
        indicator = alert.get("indicator", "positive")
        alert_layer = alert.get("layer", "")

        blast = self._blast_radius(node_id)
        impacted_count = int(blast.get("impacted_count", 0))
        recent_events = self._node_recent_events(node_id, minutes=30)
        non_positive = [e for e in recent_events if e.get("indicator") in ("negative", "attack")]

        priority = self._priority(alert_layer, indicator, impacted_count)
        return {
            "agent": self.name,
            "focus_layer": self.focus_layer,
            "priority": priority,
            "node_id": node_id,
            "alert_layer": alert_layer,
            "indicator": indicator,
            "impacted_count": impacted_count,
            "recent_event_count": len(recent_events),
            "recent_non_positive_count": len(non_positive),
            "observation": (
                f"{self.name} observed indicator={indicator}, "
                f"blast_radius={impacted_count}, node_recent_non_positive={len(non_positive)}"
            ),
            "recommended_actions": [
                f"Inspect node {node_id} telemetry for layer {self.focus_layer}",
                "Check related dependencies from blast radius",
                "Escalate if indicator remains non-positive for 3+ consecutive cycles",
            ],
        }

