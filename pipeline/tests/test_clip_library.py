from pathlib import Path

import pipeline.clip_library as cl


def test_load_index_missing_returns_empty_skeleton(tmp_path):
    data = cl.load_index(tmp_path)
    assert data == {"version": cl.INDEX_VERSION, "clips": []}


def test_save_then_load_roundtrip_sorted(tmp_path):
    cl.save_index(tmp_path, {"version": 1, "clips": [
        {"id": "zeta", "file": "clips/zeta.mp4", "tags": [], "description": "z"},
        {"id": "alpha", "file": "clips/alpha.mp4", "tags": [], "description": "a"},
    ]})
    data = cl.load_index(tmp_path)
    assert [c["id"] for c in data["clips"]] == ["alpha", "zeta"]
    assert (tmp_path / "index.json").exists()


def test_slugify():
    assert cl.slugify("Flux de Données ! bleu") == "flux-de-donnees-bleu"
    assert cl.slugify("") == "clip"
