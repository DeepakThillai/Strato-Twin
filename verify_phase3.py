"""
Phase 3 verification:
- model artifacts exist
- ML sidecar responds
- Tool API responds
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / "ml-sidecar" / "models"


def main() -> int:
    print("=" * 60)
    print("StratoTwin Phase 3 Verification")
    print("=" * 60)

    manifest = MODELS_DIR / "manifest.json"
    if not manifest.exists():
        print("[ERROR] missing model manifest")
        return 1

    data = json.loads(manifest.read_text(encoding="utf-8"))
    print(f"[Models] registered={len(data)}")
    if len(data) < 6:
        print("[ERROR] expected 6 model registrations")
        return 1

    with httpx.Client(timeout=5.0) as client:
        ml = client.get("http://127.0.0.1:8090/health")
        print(f"[ML] /health status={ml.status_code}")
        if ml.status_code != 200:
            return 1

        pred = client.post(
            "http://127.0.0.1:8090/predict/NET-ISO-V1",
            json={"features": {"packet_rate": 1200, "syn_rate": 200, "conn_rate": 450, "bw_util": 55, "port_scan_score": 0.2}},
        )
        print(f"[ML] /predict status={pred.status_code}")
        if pred.status_code != 200:
            return 1

        api_h = client.get("http://127.0.0.1:8080/health")
        print(f"[API] /health status={api_h.status_code}")
        if api_h.status_code != 200:
            return 1

        topo = client.get("http://127.0.0.1:8080/topology")
        print(f"[API] /topology status={topo.status_code}")
        if topo.status_code != 200:
            return 1

        blast = client.get("http://127.0.0.1:8080/blast-radius/L6-CHN-RACK-01")
        print(f"[API] /blast-radius status={blast.status_code}")
        if blast.status_code != 200:
            return 1

    print("\n[SUCCESS] PHASE 3 SERVICES ARE HEALTHY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

