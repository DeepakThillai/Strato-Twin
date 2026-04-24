"""
Deterministic router for selecting layer agents.
"""
from __future__ import annotations

from typing import Dict, List


class RouterAgent:
    ROUTES = {
        "L1": ["NetworkAgent", "ApplicationAgent", "ComputeAgent"],
        "L2": ["ComputeAgent", "ApplicationAgent", "FacilitiesAgent"],
        "L3": ["ApplicationAgent", "DataAgent", "NetworkAgent"],
        "L4": ["DataAgent", "ApplicationAgent", "WorkforceAgent"],
        "L5": ["WorkforceAgent", "DataAgent", "ApplicationAgent"],
        "L6": ["FacilitiesAgent", "ComputeAgent", "NetworkAgent"],
    }

    def route(self, alert: Dict[str, str]) -> List[str]:
        layer = alert.get("layer", "L1")
        indicator = alert.get("indicator", "positive")
        selected = list(self.ROUTES.get(layer, ["NetworkAgent", "ApplicationAgent"]))

        # Escalate breadth for attack-like indicators.
        if indicator == "attack":
            for extra in ["NetworkAgent", "ApplicationAgent", "DataAgent"]:
                if extra not in selected:
                    selected.append(extra)
        return selected

