"""
Phase 6 helper (Superset Agent Builder):
- validates Tool API
- builds Agent Builder import payload from local endpoints
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
SUPERSET_DIR = ROOT / "superset"
TOOLS_FILE = SUPERSET_DIR / "agent_builder_tools.json"
PAYLOAD_FILE = SUPERSET_DIR / "agent_builder_import_payload.json"
API_BASE = "http://127.0.0.1:8080"


def _discover_paths(client: httpx.Client) -> set[str]:
    try:
        r = client.get(f"{API_BASE}/openapi.json")
        if r.status_code == 200:
            data = r.json()
            return set((data or {}).get("paths", {}).keys())
    except Exception:
        pass
    return set()


def check_api() -> dict:
    with httpx.Client(timeout=6.0) as client:
        r = client.get(f"{API_BASE}/health")
        r.raise_for_status()

        paths = _discover_paths(client)
        has_query = "/query" in paths

        # Probe /query even if OpenAPI is unavailable or stale.
        query_probe = client.post(
            f"{API_BASE}/query",
            json={"question": "What's the blast radius if L6-CHN-RACK-01 fails?"},
        )
        if query_probe.status_code == 200:
            has_query = True

        if has_query:
            query_probe.raise_for_status()
            return {"mode": "full", "query_endpoint": True}

        # Compatibility mode for older API process without /query.
        br = client.get(f"{API_BASE}/blast-radius/L6-CHN-RACK-01")
        topo = client.get(f"{API_BASE}/topology")
        if br.status_code != 200 or topo.status_code != 200:
            raise RuntimeError(
                "Tool API reachable but neither /query nor deterministic fallback endpoints are usable."
            )
        return {"mode": "compat", "query_endpoint": False}


def build_payload() -> dict:
    data = json.loads(TOOLS_FILE.read_text(encoding="utf-8"))
    payload = {
        "toolset_name": data["name"],
        "description": data["description"],
        "connection": {
            "base_url": data["base_urls"]["docker_from_superset"],
            "auth_type": "none"
        },
        "tools": data["tools"],
        "sample_queries": data.get("sample_queries", []),
    }
    return payload


def main() -> int:
    SUPERSET_DIR.mkdir(parents=True, exist_ok=True)
    if not TOOLS_FILE.exists():
        print(f"[ERROR] Missing file: {TOOLS_FILE}")
        return 1

    try:
        api_status = check_api()
    except Exception as e:
        print(f"[ERROR] API validation failed: {e}")
        return 1

    payload = build_payload()
    PAYLOAD_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("[SUCCESS] Phase 6 payload ready")
    print(f"[INFO] Payload file: {PAYLOAD_FILE}")
    if api_status["mode"] == "compat":
        print("[WARN] Running API process does not expose /query yet (compat mode).")
        print("[WARN] Restart Phase 3 Tool API to enable natural-language query tool.")
    print("[INFO] Import this payload into Superset Agent Builder tools configuration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

