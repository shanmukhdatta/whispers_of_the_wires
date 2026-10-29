"""Mentor dashboard backend: library, playlists, settings and instrument/genre controls."""
from fastapi.testclient import TestClient
from wow.api import app
from wow.planning import PlanningRequest, build_blueprint
from wow.composer import compose_rule_based


def test_genres_and_custom_instruments_are_real_controls():
    plain = build_blueprint(PlanningRequest(prompt="peaceful", genre="ambient"))
    assert plain.genre == "ambient"
    custom = build_blueprint(
        PlanningRequest(prompt="peaceful", genre="electronic",
                        instrument_programs={"melody": 80, "bass": 38})
    )
    assert [x.program for x in custom.tracks] == [80, 48, 38, 0]
    assert custom.genre == "electronic"
    # Genre settings alter actual note count/velocities, not merely UI labels.
    assert len(compose_rule_based(plain).instruments[0].notes) != (
        len(compose_rule_based(custom).instruments[0].notes)
    )


def test_library_playlist_and_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    planned = client.post(
        "/api/v1/blueprints",
        json={"prompt": "a quiet place", "genre": "ambient",
              "instrument_programs": {"melody": 11}},
    )
    assert planned.status_code == 200, planned.text
    job = client.post("/api/v1/jobs", json=planned.json())
    assert job.status_code == 202, job.text
    cid = job.json()["job_id"]
    results = client.get("/api/v1/library")
    assert results.status_code == 200
    assert results.json()["items"][0]["genre"] == "ambient"
    assert not results.json()["items"][0]["favorite"]
    assert client.put(f"/api/v1/library/{cid}/favorite",
                      json={"favorite": True}).status_code == 200
    assert client.get("/api/v1/library").json()["items"][0]["favorite"]
    playlist = client.post("/api/v1/playlists", json={"name": "My study music"})
    assert playlist.status_code == 201
    pid = playlist.json()["id"]
    assert client.post(f"/api/v1/playlists/{pid}/items",
                       json={"composition_id": cid}).status_code == 200
    assert cid in client.get("/api/v1/playlists").json()["items"][0]["items"]
    assert client.delete(f"/api/v1/playlists/{pid}/items/{cid}").status_code == 200
    assert client.put("/api/v1/settings",
                      json={"default_genre": "jazz", "default_tempo": 110,
                            "listen_volume": 70, "default_provider": "rule_based"}
                      ).status_code == 200
    assert client.get("/api/v1/settings").json()["default_tempo"] == 110
    assert client.get("/api/v1/library?limit=0").status_code == 422
