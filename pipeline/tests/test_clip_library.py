from pathlib import Path

import pytest

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


@pytest.fixture
def fake_mp4(tmp_path):
    """Petit fichier factice tenant lieu de mp4 (on teste copie/index, pas l'encodage)."""
    src = tmp_path / "src.mp4"
    src.write_bytes(b"FAKEMP4DATA")
    return src


def test_add_clip_copies_and_registers(tmp_path, fake_mp4, monkeypatch):
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    root = tmp_path / "lib"
    entry = cl.add_clip(root, fake_mp4, ["flux-donnees", "bleu"], "Flux bleus",
                        model="kling-turbo", cost_usd=0.35)
    assert entry["id"] == "flux-bleus"
    assert (root / "clips" / "flux-bleus.mp4").read_bytes() == b"FAKEMP4DATA"
    assert entry["tags"] == ["flux-donnees", "bleu"]
    assert entry["model"] == "kling-turbo" and entry["cost_usd"] == 0.35
    assert "thumb" not in entry
    assert [c["id"] for c in cl.load_index(root)["clips"]] == ["flux-bleus"]


def test_add_clip_idempotent_on_same_id(tmp_path, fake_mp4, monkeypatch):
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    root = tmp_path / "lib"
    cl.add_clip(root, fake_mp4, ["a"], "desc 1", clip_id="fixe")
    cl.add_clip(root, fake_mp4, ["a", "b"], "desc 2", clip_id="fixe")
    clips = cl.load_index(root)["clips"]
    assert len(clips) == 1
    assert clips[0]["description"] == "desc 2"
    assert clips[0]["tags"] == ["a", "b"]


def test_add_clip_auto_id_collision_suffix(tmp_path, fake_mp4, monkeypatch):
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    root = tmp_path / "lib"
    a = cl.add_clip(root, fake_mp4, ["x"], "Même titre")
    b = cl.add_clip(root, fake_mp4, ["x"], "Même titre")
    assert a["id"] == "meme-titre"
    assert b["id"] == "meme-titre-02"
    assert len(cl.load_index(root)["clips"]) == 2
