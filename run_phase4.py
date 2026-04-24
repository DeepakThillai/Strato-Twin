"""
Runs Phase 4 orchestration loop.
Requires Phase 3 APIs to be running.
"""
from __future__ import annotations

import time

from agents.orchestrator import IncidentOrchestrator


def main() -> int:
    orchestrator = IncidentOrchestrator()
    print("[START] Phase 4 orchestrator running (poll every 10s). Press Ctrl+C to stop.")
    try:
        while True:
            incidents = orchestrator.process_recent_alerts(limit=30, max_new=10)
            if incidents:
                print(f"[INFO] Created incidents={len(incidents)}")
                for inc in incidents:
                    print(
                        f"  - incident_id={inc['incident_id']} severity={inc['severity']} "
                        f"node={inc.get('node_id')}"
                    )
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n[STOP] Phase 4 orchestrator stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

