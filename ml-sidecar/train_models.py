"""
Phase 3 model training for StratoTwin.
Creates lightweight model artifacts for ML sidecar inference.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / "models"


def train_net_iso() -> str:
    rng = np.random.default_rng(42)
    x = rng.normal(loc=0.0, scale=1.0, size=(2000, 5))
    model = IsolationForest(n_estimators=120, contamination=0.03, random_state=42)
    model.fit(x)
    path = MODELS_DIR / "NET-ISO-V1.joblib"
    joblib.dump({"model": model}, path)
    return str(path)


def train_net_lstm_proxy() -> str:
    rng = np.random.default_rng(43)
    baseline = rng.normal(loc=5000.0, scale=1200.0, size=(4000,))
    stats = {
        "mean": float(np.mean(baseline)),
        "std": float(np.std(baseline) + 1e-6),
        "window": 20,
        "threshold_z": 3.0,
    }
    path = MODELS_DIR / "NET-LSTM-V1.joblib"
    joblib.dump(stats, path)
    return str(path)


def train_compute_autoencoder_proxy() -> str:
    rng = np.random.default_rng(44)
    x = rng.normal(0, 1, size=(3000, 128))
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
    pca = PCA(n_components=24, random_state=44)
    pca.fit(x_scaled)
    path = MODELS_DIR / "COMPUTE-SYSCALL-AE-V1.joblib"
    joblib.dump({"scaler": scaler, "pca": pca, "threshold": 1.25}, path)
    return str(path)


def train_app_abuse_iso() -> str:
    rng = np.random.default_rng(45)
    x = np.column_stack(
        [
            rng.normal(800, 300, size=2000),   # rps
            rng.normal(40, 15, size=2000),     # unique_endpoints
            rng.normal(0.02, 0.01, size=2000), # error_rate
            rng.normal(120, 60, size=2000),    # source_ip_count
        ]
    )
    model = IsolationForest(n_estimators=140, contamination=0.04, random_state=45)
    model.fit(x)
    path = MODELS_DIR / "APP-ABUSE-ISO-V1.joblib"
    joblib.dump({"model": model}, path)
    return str(path)


def train_workforce_rf() -> str:
    rng = np.random.default_rng(46)
    x = rng.normal(size=(2500, 8))
    risk = (
        (x[:, 0] < -0.3).astype(int)
        + (x[:, 1] > 0.8).astype(int)
        + (x[:, 3] < -0.8).astype(int)
        + (x[:, 7] > 0.7).astype(int)
    )
    y = (risk >= 2).astype(int)
    model = RandomForestClassifier(n_estimators=180, random_state=46)
    model.fit(x, y)
    path = MODELS_DIR / "WRK-ATTRITION-RF-V1.joblib"
    joblib.dump({"model": model}, path)
    return str(path)


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "NET-ISO-V1": train_net_iso(),
        "NET-LSTM-V1": train_net_lstm_proxy(),
        "COMPUTE-SYSCALL-AE-V1": train_compute_autoencoder_proxy(),
        "APP-ABUSE-ISO-V1": train_app_abuse_iso(),
        "DATA-ACCESS-VOL-V1": "zscore-runtime",
        "WRK-ATTRITION-RF-V1": train_workforce_rf(),
    }
    with open(MODELS_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(artifacts, f, indent=2)
    print("[SUCCESS] Trained Phase 3 model artifacts")
    print(f"[INFO] Models directory: {MODELS_DIR}")


if __name__ == "__main__":
    main()

