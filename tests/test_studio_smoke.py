"""Streamlit initial dashboard must render without requiring a running API."""
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_studio_initial_render_does_not_crash():
    root = Path(__file__).resolve().parents[1]
    at = AppTest.from_file(str(root / "studio_v2.py"), default_timeout=25).run()
    assert len(at.exception) == 0
    assert "WHISPERS OF THE WIRES" in at.title[0].value
    assert len(at.tabs) == 4
