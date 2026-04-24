"""
Phase 5 runner:
- installs dashboard deps
- starts Vite dev server on port 3000
Requires Phase 3 API (8080) running for live data.
"""
from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
DASHBOARD_DIR = os.path.join(ROOT, "dashboard")


def run(cmd: list[str]) -> int:
    print(f"[RUN] {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=DASHBOARD_DIR)


def main() -> int:
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    if run([npm_cmd, "install"]) != 0:
        print("[ERROR] npm install failed")
        return 1
    return run([npm_cmd, "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"])


if __name__ == "__main__":
    raise SystemExit(main())

