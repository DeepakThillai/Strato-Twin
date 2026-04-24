"""
StratoTwin ML sidecar API (Phase 3).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / "models"

app = FastAPI(title="StratoTwin ML Sidecar", version="0.1.0")
MODEL_CACHE: Dict[str, Any] = {}
DATA_VOL_BASELINE = {"mean": 12000.0, "std": 3500.0}


FEATURES = {
    "NET-ISO-V1": ["packet_rate", "syn_rate", "conn_rate", "bw_util", "port_scan_score"],
    "NET-LSTM-V1": ["outbound_bytes_per_sec"],
    "COMPUTE-SYSCALL-AE-V1": ["syscall_vector_128dim"],
    "APP-ABUSE-ISO-V1": ["rps", "unique_endpoints", "error_rate", "source_ip_count"],
    "DATA-ACCESS-VOL-V1": ["records_accessed_per_session"],
    "WRK-ATTRITION-RF-V1": [
        "tenure_days",
        "bench_duration_days",
        "perf_flag_count_90d",
        "cert_count",
        "project_count_12m",
        "manager_change_flag",
        "salary_band_vs_market",
        "last_promotion_days",
    ],
}


class PredictRequest(BaseModel):
    features: Dict[str, Any] = Field(default_factory=dict)


def _load_artifact(name: str) -> Any:
    path = MODELS_DIR / f"{name}.joblib"
    if not path.exists():
        return None
    return joblib.load(path)


def _to_array(values: List[float]) -> np.ndarray:
    return np.array(values, dtype=float).reshape(1, -1)


def _predict(model_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
    if model_id == "DATA-ACCESS-VOL-V1":
        value = float(features.get("records_accessed_per_session", 0.0))
        z = abs((value - DATA_VOL_BASELINE["mean"]) / (DATA_VOL_BASELINE["std"] + 1e-6))
        return {"score": float(z), "anomaly": z > 3.0}

    artifact = MODEL_CACHE.get(model_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail=f"Model artifact missing: {model_id}")

    if model_id in ("NET-ISO-V1", "APP-ABUSE-ISO-V1"):
        values = [float(features.get(k, 0.0)) for k in FEATURES[model_id]]
        x = _to_array(values)
        model = artifact["model"]
        score = float(-model.decision_function(x)[0])
        pred = int(model.predict(x)[0])  # -1 anomaly, 1 normal
        return {"score": score, "anomaly": pred == -1}

    if model_id == "NET-LSTM-V1":
        value = float(features.get("outbound_bytes_per_sec", 0.0))
        mean = float(artifact["mean"])
        std = float(artifact["std"])
        z = abs((value - mean) / (std + 1e-6))
        return {"score": float(z), "anomaly": z > float(artifact["threshold_z"])}

    if model_id == "COMPUTE-SYSCALL-AE-V1":
        raw = features.get("syscall_vector_128dim", [])
        if not isinstance(raw, list) or len(raw) != 128:
            raise HTTPException(status_code=400, detail="syscall_vector_128dim must be length-128 array")
        x = np.array(raw, dtype=float).reshape(1, -1)
        scaler = artifact["scaler"]
        pca = artifact["pca"]
        x_scaled = scaler.transform(x)
        x_recon = pca.inverse_transform(pca.transform(x_scaled))
        err = float(np.mean(np.square(x_scaled - x_recon)))
        return {"score": err, "anomaly": err > float(artifact["threshold"])}

    if model_id == "WRK-ATTRITION-RF-V1":
        values = [float(features.get(k, 0.0)) for k in FEATURES[model_id]]
        x = _to_array(values)
        model = artifact["model"]
        proba = float(model.predict_proba(x)[0][1])
        return {"score": proba, "anomaly": proba > 0.8}

    raise HTTPException(status_code=400, detail=f"Unsupported model_id: {model_id}")


@app.on_event("startup")
def startup() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for model_id in FEATURES.keys():
        MODEL_CACHE[model_id] = _load_artifact(model_id)


@app.get("/health")
def health() -> Dict[str, Any]:
    loaded = [mid for mid, obj in MODEL_CACHE.items() if obj is not None or mid == "DATA-ACCESS-VOL-V1"]
    return {"status": "ok", "loaded_models": loaded, "loaded_count": len(loaded)}


@app.get("/models")
def models() -> Dict[str, Any]:
    return {"models": list(FEATURES.keys())}


@app.post("/predict/{model_id}")
def predict(model_id: str, req: PredictRequest) -> Dict[str, Any]:
    if model_id not in FEATURES:
        raise HTTPException(status_code=404, detail="Unknown model_id")
    result = _predict(model_id, req.features)
    indicator = "attack" if result["anomaly"] else "positive"
    return {"model_id": model_id, "indicator": indicator, **result}

