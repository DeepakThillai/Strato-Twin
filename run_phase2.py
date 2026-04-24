"""
Launches all Phase 2 services as local Python processes.
Press Ctrl+C to stop all children.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.dirname(__file__))

COMMANDS = [
    [sys.executable, os.path.join(ROOT, "process-engine", "main.py")],
    [sys.executable, os.path.join(ROOT, "simulators", "network", "main.py")],
    [sys.executable, os.path.join(ROOT, "simulators", "compute", "main.py")],
    [sys.executable, os.path.join(ROOT, "simulators", "application", "main.py")],
    [sys.executable, os.path.join(ROOT, "simulators", "data", "main.py")],
    [sys.executable, os.path.join(ROOT, "simulators", "workforce", "main.py")],
    [sys.executable, os.path.join(ROOT, "simulators", "facilities", "main.py")],
]


def check_dependencies() -> bool:
    required = {
        "kafka": "kafka-python",
        "pymongo": "pymongo",
    }
    missing = []
    for module_name, package_name in required.items():
        try:
            __import__(module_name)
        except Exception:
            missing.append(package_name)

    if not missing:
        return True

    unique = sorted(set(missing))
    print("[ERROR] Missing Python dependencies: " + ", ".join(unique))
    print("[INFO] Install with:")
    print(f"  {sys.executable} -m pip install -r requirements.txt")
    return False


def main() -> int:
    if not check_dependencies():
        return 1

    children = []
    try:
        for cmd in COMMANDS:
            p = subprocess.Popen(cmd, cwd=ROOT)
            children.append(p)
            print(f"[START] pid={p.pid} cmd={' '.join(cmd)}")
            time.sleep(0.2)
        print("[READY] Phase 2 pipeline running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            for p in children:
                if p.poll() is not None:
                    print(f"[ERROR] process exited pid={p.pid} code={p.returncode}")
                    return 1
    except KeyboardInterrupt:
        print("\n[STOP] stopping all phase2 processes...")
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

