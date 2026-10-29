"""Blinding, generated-artifact provenance and real-ratings-only analysis."""
import csv
import json
import zipfile

import pytest

from wow.contracts import default_blueprint
from wow.generation import GenerationService
from wow.listener_study import analyze_study, build_study


def test_blind_pack_has_no_provider_labels_and_keeps_private_key(tmp_path):
    service = GenerationService(tmp_path / "workspace")
    a = service.create(default_blueprint("Peaceful morning"))
    b = service.create(default_blueprint("Joyful evening"))
    assert a["state"] == b["state"] == "completed"
    result = build_study(service.root, tmp_path / "study", seed=12)
    key = json.loads((tmp_path / "study" / "PRIVATE_stimulus_key.json").read_text())
    assert len(key) == result["stimuli"] == 2
    with zipfile.ZipFile(result["zip"]) as archive:
        names = archive.namelist()
        assert "PRIVATE_stimulus_key.json" not in names
        assert len([n for n in names if n.endswith(".wav")]) == 2
        assert not any("rule_based" in n for n in names)


def test_real_ratings_analyzed_with_duplicate_rejection(tmp_path):
    service = GenerationService(tmp_path / "workspace")
    service.create(default_blueprint("Sorrow then peace"))
    service.create(default_blueprint("Excited then joyful"))
    result = build_study(service.root, tmp_path / "study")
    key = json.loads(open(result["private_key"], encoding="utf-8").read())
    data = tmp_path / "genuine_ratings.csv"
    with data.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["stimulus_id", "participant_code", "mood_match", "musical_coherence"])
        writer.writerow([key[0]["stimulus_id"], "anonymous-01", 4, 5])
        writer.writerow([key[1]["stimulus_id"], "anonymous-01", 3, 3])
    summary = analyze_study(result["private_key"], data)
    assert summary["rating_records"] == 2
    assert summary["by_provider"][0]["insufficient_pilot_data"]
    with data.open("a", encoding="utf-8") as f:
        f.write(f"{key[0]['stimulus_id']},anonymous-01,4,5\n")
    with pytest.raises(ValueError, match="Duplicate"):
        analyze_study(result["private_key"], data)
