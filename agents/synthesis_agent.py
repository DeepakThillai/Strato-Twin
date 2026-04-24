"""
Synthesis agent for cross-layer incident report generation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List


class SynthesisAgent:
    @staticmethod
    def _incident_severity(alert_indicator: str, findings: List[Dict[str, Any]]) -> str:
        if alert_indicator == "attack":
            return "critical"
        if any(f.get("priority") == "critical" for f in findings):
            return "critical"
        if any(f.get("priority") == "high" for f in findings):
            return "high"
        return "medium"

    def synthesize(self, alert: Dict[str, Any], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        severity = self._incident_severity(alert.get("indicator", "positive"), findings)
        impacted = max([int(f.get("impacted_count", 0)) for f in findings] + [0])

        report = {
            "incident_id": f"inc-{uuid.uuid4()}",
            "source_execution_id": alert.get("execution_id"),
            "created_at": datetime.now(timezone.utc),
            "severity": severity,
            "indicator": alert.get("indicator", "positive"),
            "layer": alert.get("layer"),
            "node_id": alert.get("node_id"),
            "site": alert.get("site"),
            "summary": (
                f"Cross-layer synthesis for node={alert.get('node_id')} "
                f"indicator={alert.get('indicator')} impacted_nodes={impacted}"
            ),
            "selected_agents": [f.get("agent") for f in findings],
            "findings": findings,
            "recommended_actions": [
                "Apply immediate containment on affected node",
                "Validate downstream dependencies from blast radius",
                "Track recurrence in process_executions over next 15 minutes",
            ],
        }
        return report

