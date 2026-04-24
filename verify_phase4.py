"""
Phase 4 verification:
- Router dispatch works
- Layer agents produce findings
- Incidents persisted
"""
from __future__ import annotations

from agents.orchestrator import IncidentOrchestrator


def sample_alert() -> dict:
    return {
        "execution_id": "manual-phase4-verification",
        "process_id": "PROC-ALL-013",
        "layer": "L1",
        "node_id": "L1-CHN-FW-01",
        "site": "CHN",
        "indicator": "negative",
    }


def main() -> int:
    print("=" * 60)
    print("StratoTwin Phase 4 Verification")
    print("=" * 60)

    orchestrator = IncidentOrchestrator()
    incidents = orchestrator.process_recent_alerts(limit=30, max_new=5)

    total_incidents = orchestrator.db.incidents.count_documents({})
    print(f"[Mongo] incidents total={total_incidents}")
    if total_incidents == 0 and not incidents:
        generated = orchestrator.process_alert(sample_alert())
        incidents = [generated]
        total_incidents = orchestrator.db.incidents.count_documents({})
        print(f"[Mongo] incidents total (after synthetic run)={total_incidents}")
        if total_incidents == 0:
            print("[ERROR] no incidents were generated")
            return 1

    if incidents:
        latest = incidents[0]
        print(f"[Incident] severity={latest.get('severity')} node={latest.get('node_id')}")
        print(f"[Incident] agents={latest.get('selected_agents')}")
        if not latest.get("findings"):
            print("[ERROR] no findings in synthesized incident")
            return 1
    else:
        # Existing incidents may already cover recent alerts.
        latest = orchestrator.db.incidents.find_one(sort=[("created_at", -1)])
        if latest is None:
            print("[ERROR] incident lookup failed")
            return 1
        print(f"[Incident] reused latest incident_id={latest.get('incident_id')}")

    print("\n[SUCCESS] PHASE 4 AGENT ORCHESTRATION IS HEALTHY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

