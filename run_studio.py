"""Launch local FastAPI and Streamlit studio in one terminal (localhost only)."""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "wow.api:app",
         "--host", "127.0.0.1", "--port", "8000"],
        cwd=root,
    )
    try:
        for _ in range(30):
            if api.poll() is not None:
                raise RuntimeError("Backend exited before startup")
            try:
                with urllib.request.urlopen(
                    "http://127.0.0.1:8000/health", timeout=0.5
                ) as response:
                    if response.status == 200:
                        break
            except (urllib.error.URLError, OSError):
                time.sleep(0.2)
        else:
            raise RuntimeError("Backend health check did not succeed")
        print("API ready at http://127.0.0.1:8000/docs")
        print("Opening Streamlit at http://localhost:8501")
        return subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "studio_v2.py",
             "--server.address", "127.0.0.1", "--server.port", "8501"],
            cwd=root, check=False,
        ).returncode
    except KeyboardInterrupt:
        return 0
    finally:
        if api.poll() is None:
            api.terminate()
            try:
                api.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api.kill()
                api.wait()


if __name__ == "__main__":
    raise SystemExit(main())
