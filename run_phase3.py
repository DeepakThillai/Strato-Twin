"""
Runs Phase 3 services:
1) Train models
2) Start ML sidecar (8090)
3) Start tool API (8080)
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.dirname(__file__))


def run_train() -> int:
    cmd = [sys.executable, os.path.join(ROOT, "ml-sidecar", "train_models.py")]
    print(f"[RUN] {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    if run_train() != 0:
        print("[ERROR] Model training failed")
        return 1

    children = []
    try:
        commands = [
            [sys.executable, "-m", "uvicorn", "main:app", "--app-dir", os.path.join(ROOT, "ml-sidecar"), "--host", "0.0.0.0", "--port", "8090"],
            [sys.executable, "-m", "uvicorn", "main:app", "--app-dir", os.path.join(ROOT, "api"), "--host", "0.0.0.0", "--port", "8080"],
        ]
        for cmd in commands:
            p = subprocess.Popen(cmd, cwd=ROOT)
            children.append(p)
            print(f"[START] pid={p.pid} cmd={' '.join(cmd)}")
            time.sleep(0.2)
        print("[READY] Phase 3 services running. Press Ctrl+C to stop.")

        while True:
            time.sleep(1)
            for p in children:
                if p.poll() is not None:
                    print(f"[ERROR] process exited pid={p.pid} code={p.returncode}")
                    return 1
    except KeyboardInterrupt:
        print("\n[STOP] stopping phase3 services...")
        return 0
    finally:
        for p in children:
            if p.poll() is None:
                p.send_signal(signal.SIGTERM)
        time.sleep(1)
        for p in children:
            if p.poll() is None:
                p.kill()


if __name__ == "__main__":
    raise SystemExit(main())

