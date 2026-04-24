"""
Phase 6 verification (Superset Agent Builder):
- Agent Builder tool manifest exists
- Tool API supports /query (full mode) or deterministic fallback endpoints (compat mode)
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
TOOLS_FILE = ROOT / "superset" / "agent_builder_tools.json"
API_BASE = "http://127.0.0.1:8080"


def _discover_paths(client: httpx.Client) -> set[str]:
    try:
        r = client.get(f"{API_BASE}/openapi.json")
        if r.status_code == 200:
            return set((r.json() or {}).get("paths", {}).keys())
    except Exception:
        pass
    return set()


def main() -> int:
    print("=" * 60)
    print("StratoTwin Phase 6 Verification")
    print("=" * 60)

    if not TOOLS_FILE.exists():
        print(f"[ERROR] missing manifest: {TOOLS_FILE}")
        return 1
    data = json.loads(TOOLS_FILE.read_text(encoding="utf-8"))
    tools = data.get("tools", [])
    print(f"[Manifest] tools={len(tools)}")
    if len(tools) < 3:
        print("[ERROR] insufficient tools in manifest")
        return 1

    try:
        with httpx.Client(timeout=8.0) as client:
            health = client.get(f"{API_BASE}/health")
            print(f"[API] /health status={health.status_code}")
            if health.status_code != 200:
                return 1

            paths = _discover_paths(client)
            has_query = "/query" in paths

            q1 = client.post(
                f"{API_BASE}/query",
                json={"question": "What's the blast radius if L6-CHN-RACK-01 fails?"},
            )
            print(f"[API] /query blast status={q1.status_code}")
            if q1.status_code == 200:
                has_query = True
                result = q1.json()
                impacted = (((result or {}).get("result") or {}).get("impacted_count")) if result.get("ok") else None
                print(f"[API] blast impacted_count={impacted}")
                q2 = client.post(f"{API_BASE}/query", json={"question": "show me topology summary"})
                print(f"[API] /query topology status={q2.status_code}")
                if q2.status_code != 200:
                    return 1
            else:
                br = client.get(f"{API_BASE}/blast-radius/L6-CHN-RACK-01")
                topo = client.get(f"{API_BASE}/topology")
                print(f"[API] /blast-radius status={br.status_code}")
                print(f"[API] /topology status={topo.status_code}")
                if br.status_code != 200 or topo.status_code != 200:
                    return 1
                print("[WARN] /query endpoint unavailable on currently running API process.")
                print("[WARN] Deterministic tools work; restart Tool API for full NL-query mode.")
    except httpx.HTTPError as e:
        print(f"[ERROR] Could not reach Tool API at {API_BASE}: {e}")
        print("[INFO] Start Phase 3 API first, then rerun verification.")
        return 1

    if has_query:
        print("\n[SUCCESS] PHASE 6 AGENT BUILDER ASSETS READY (FULL MODE)")
    else:
        print("\n[SUCCESS] PHASE 6 AGENT BUILDER ASSETS READY (COMPAT MODE)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

