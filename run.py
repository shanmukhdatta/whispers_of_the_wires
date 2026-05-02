#!/usr/bin/env python3
"""
Whispers of the Wires - Entry Point
Run this script to start the application.
"""
import os
import sys
import subprocess
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.resolve()
APP_DIR = PROJECT_ROOT / "app"

def check_dependencies():
    """Check if required packages are installed."""
    required = ["streamlit", "numpy", "Pillow"]
    missing = []

    for pkg in required:
        try:
            __import__(pkg.lower())
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed!")

def main():
    """Run the Streamlit application."""
    print("=" * 60)
    print("🎵 Whispers of the Wires - AI Music Composer")
    print("=" * 60)
    print()

    # Check dependencies
    check_dependencies()

    # Add project root to path
    sys.path.insert(0, str(PROJECT_ROOT))

    # Run Streamlit
    main_script = APP_DIR / "main.py"

    print(f"Starting app from: {main_script}")
    print("Opening browser...")
    print()

    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(main_script),
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--theme.base", "dark",
    ]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
