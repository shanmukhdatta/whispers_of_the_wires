"""Selective edits must preserve notes in all locked tracks and bars."""
import pretty_midi
from fastapi.testclient import TestClient

from wow.api import app
from wow.composer import compose_rule_based
from wow.contracts import default_blueprint
from wow.editing import EditRequest, locked_events, selective_edit


def test_locked_notes_unchanged():
    bp = default_blueprint("a musical journey")
    old = compose_rule_based(bp)
    req = EditRequest(base_version=1, track_ids=["harmony"], start_bar=4,
                      end_bar_exclusive=8, operation="more_energy")
    start = 4 * 4 * 60 / bp.tempo_bpm
    end = 8 * 4 * 60 / bp.tempo_bpm
    new = selective_edit(old, bp, req)
    assert locked_events(old, tracks={"harmony"}, start=start, end=end) == (
        locked_events(new, tracks={"harmony"}, start=start, end=end)
    )
    assert sum(x.velocity for x in old.instruments[1].notes) != (
        sum(x.velocity for x in new.instruments[1].notes)
    )


def test_reject_unknown_track_and_out_of_range():
    bp = default_blueprint("test")
    orig = compose_rule_based(bp)
    for track, end in [("invalid", 8), ("melody", 24)]:
        request = EditRequest(track_ids=[track], start_bar=4,
                              end_bar_exclusive=end, operation="more_energy")
        try:
            selective_edit(orig, bp, request)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid edit accepted")


def test_versioned_api(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    created = client.post("/api/v1/jobs", json=default_blueprint("demo").model_dump())
    assert created.status_code == 202
    job = created.json()["job_id"]
    edit = client.post(f"/api/v1/compositions/{job}/edits", json={
        "base_version": 1, "track_ids": ["harmony"], "start_bar": 4,
        "end_bar_exclusive": 8, "operation": "more_energy",
    })
    assert edit.status_code == 200, edit.text
    assert edit.json()["version"] == 2
    assert client.get(f"/api/v1/compositions/{job}/versions").json()["versions"] == [1, 2]
    assert client.get(
        f"/api/v1/compositions/{job}/assets/composition.mid", params={"version": 2}
    ).status_code == 200
    stale = client.post(f"/api/v1/compositions/{job}/edits", json={
        "base_version": 1, "track_ids": ["harmony"], "start_bar": 4,
        "end_bar_exclusive": 8, "operation": "more_energy",
    })
    assert stale.status_code == 422
