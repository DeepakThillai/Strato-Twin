"""
Phase 5 verification:
- Dashboard source files exist
- Tool API exposes graph + websocket-compatible alert endpoint
"""
from __future__ import annotations

from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("=" * 60)
    print("StratoTwin Phase 5 Verification")
    print("=" * 60)

    required_files = [
        ROOT / "dashboard" / "package.json",
        ROOT / "dashboard" / "index.html",
        ROOT / "dashboard" / "src" / "main.tsx",
        ROOT / "dashboard" / "src" / "App.tsx",
        ROOT / "dashboard" / "src" / "api.ts",
    ]
    for f in required_files:
        if not f.exists():
            print(f"[ERROR] missing file: {f}")
            return 1

    with httpx.Client(timeout=6.0) as client:
        topo = client.get("http://127.0.0.1:8080/topology/graph")
        print(f"[API] /topology/graph status={topo.status_code}")
        if topo.status_code != 200:
            return 1
        recent = client.get("http://127.0.0.1:8080/alerts/recent?limit=5")
        print(f"[API] /alerts/recent status={recent.status_code}")
        if recent.status_code != 200:
            return 1

    print("\n[SUCCESS] PHASE 5 DASHBOARD ASSETS ARE READY")
    print("[INFO] Start dashboard with: python run_phase5.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

