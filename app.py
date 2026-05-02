#!/usr/bin/env python3
"""Direct entry point - runs without subprocess."""
import sys
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Run the app
from app.main import main

if __name__ == "__main__":
    main()
