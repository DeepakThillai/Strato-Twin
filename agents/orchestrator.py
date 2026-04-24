"""
Phase 4 LangGraph orchestrator for alert triage.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, TypedDict

import httpx
from langgraph.graph import END, StateGraph
from pymongo import MongoClient

from agents.application_agent import ApplicationAgent
from agents.compute_agent import ComputeAgent
from agents.data_agent import DataAgent
from agents.facilities_agent import FacilitiesAgent
from agents.network_agent import NetworkAgent
from agents.router_agent import RouterAgent
from agents.synthesis_agent import SynthesisAgent
from agents.workforce_agent import WorkforceAgent

MONGO_URI = "mongodb://localhost:27017"
TOOL_API_BASE = "http://127.0.0.1:8080"


class AlertState(TypedDict, total=False):
    alert: Dict[str, Any]
    selected_agents: List[str]
    findings: List[Dict[str, Any]]
    incident: Dict[str, Any]


class IncidentOrchestrator:
    def __init__(self) -> None:
        self.router = RouterAgent()
        self.synthesis = SynthesisAgent()
        self.agents = {
            "NetworkAgent": NetworkAgent(),
            "ComputeAgent": ComputeAgent(),
            "ApplicationAgent": ApplicationAgent(),
            "DataAgent": DataAgent(),
            "WorkforceAgent": WorkforceAgent(),
            "FacilitiesAgent": FacilitiesAgent(),
        }
        self.graph = self._build_graph()
        self.db = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)["stratotwin"]
        self.db.incidents.create_index("source_execution_id", unique=True)
        self.db.incidents.create_index("created_at")

    def _build_graph(self):
        graph = StateGraph(AlertState)
        graph.add_node("route", self._route_node)
        graph.add_node("analyze", self._analyze_node)
        graph.add_node("synthesize", self._synthesize_node)
        graph.set_entry_point("route")
        graph.add_edge("route", "analyze")
        graph.add_edge("analyze", "synthesize")
        graph.add_edge("synthesize", END)
        return graph.compile()

    def _route_node(self, state: AlertState) -> AlertState:
        alert = state["alert"]
        selected = self.router.route(alert)
        return {"selected_agents": selected}

    def _analyze_node(self, state: AlertState) -> AlertState:
        alert = state["alert"]
        selected = state.get("selected_agents", [])
        if not selected:
            return {"findings": []}

        def run_one(agent_name: str) -> Dict[str, Any]:
            return self.agents[agent_name].analyze(alert)

        with ThreadPoolExecutor(max_workers=len(selected)) as pool:
            findings = list(pool.map(run_one, selected))
        return {"findings": findings}

    def _synthesize_node(self, state: AlertState) -> AlertState:
        alert = state["alert"]
        findings = state.get("findings", [])
        incident = self.synthesis.synthesize(alert, findings)
        return {"incident": incident}

    def _persist_incident(self, incident: Dict[str, Any]) -> None:
        source_execution_id = incident.get("source_execution_id")
        if source_execution_id:
            self.db.incidents.update_one(
                {"source_execution_id": source_execution_id},
                {"$set": incident},
                upsert=True,
            )
        else:
            self.db.incidents.insert_one(incident)

    def process_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        result = self.graph.invoke({"alert": alert})
        incident = result["incident"]
        self._persist_incident(incident)
        return incident

    def fetch_recent_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        with httpx.Client(timeout=8.0) as client:
            response = client.get(f"{TOOL_API_BASE}/alerts/recent", params={"limit": limit})
            response.raise_for_status()
            payload = response.json()
            return payload.get("alerts", [])

    def process_recent_alerts(self, limit: int = 20, max_new: int = 5) -> List[Dict[str, Any]]:
        alerts = self.fetch_recent_alerts(limit=limit)
        incidents: List[Dict[str, Any]] = []
        processed = 0
        for alert in alerts:
            source_execution_id = alert.get("execution_id")
            if source_execution_id and self.db.incidents.find_one({"source_execution_id": source_execution_id}):
                continue
            incidents.append(self.process_alert(alert))
            processed += 1
            if processed >= max_new:
                break
        return incidents

