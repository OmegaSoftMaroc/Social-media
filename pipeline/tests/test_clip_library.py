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


def _seed(root, fake_mp4, monkeypatch):
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    cl.add_clip(root, fake_mp4, ["flux-donnees", "bleu", "push-in"],
                "Flux bleus push-in", clip_id="a2")
    cl.add_clip(root, fake_mp4, ["flux-donnees"], "Flux simple", clip_id="a1")
    cl.add_clip(root, fake_mp4, ["logo", "sting"], "Logo sting", clip_id="b1")


def test_search_ranks_by_tag_overlap(tmp_path, fake_mp4, monkeypatch):
    root = tmp_path / "lib"
    _seed(root, fake_mp4, monkeypatch)
    res = cl.search(root, tags=["flux-donnees", "bleu"])
    ids = [c["id"] for c in res]
    assert ids == ["a2", "a1"]   # a2 (2 tags communs) avant a1 (1), b1 exclu


def test_search_by_text_substring(tmp_path, fake_mp4, monkeypatch):
    root = tmp_path / "lib"
    _seed(root, fake_mp4, monkeypatch)
    res = cl.search(root, text="sting")
    assert [c["id"] for c in res] == ["b1"]


def test_get(tmp_path, fake_mp4, monkeypatch):
    root = tmp_path / "lib"
    _seed(root, fake_mp4, monkeypatch)
    assert cl.get(root, "a1")["description"] == "Flux simple"
    assert cl.get(root, "inconnu") is None


def test_reuse_copies_file(tmp_path, fake_mp4, monkeypatch):
    root = tmp_path / "lib"
    _seed(root, fake_mp4, monkeypatch)
    out = tmp_path / "out.mp4"
    cl.reuse(root, "a1", out)
    assert out.read_bytes() == b"FAKEMP4DATA"


def test_reuse_unknown_raises(tmp_path, fake_mp4, monkeypatch):
    root = tmp_path / "lib"
    _seed(root, fake_mp4, monkeypatch)
    with pytest.raises(KeyError):
        cl.reuse(root, "inconnu", tmp_path / "x.mp4")


def test_search_text_case_insensitive_on_tags(tmp_path, fake_mp4, monkeypatch):
    root = tmp_path / "lib"
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    cl.add_clip(root, fake_mp4, ["Corporate", "Bleu"], "Un clip", clip_id="c1")
    assert [c["id"] for c in cl.search(root, text="corporate")] == ["c1"]


def test_cli_add_then_search(tmp_path, fake_mp4, monkeypatch, capsys):
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    monkeypatch.setattr(cl, "DEFAULT_ROOT", tmp_path / "lib")
    assert cl._main(["add", str(fake_mp4), "--tags", "flux-donnees,bleu",
                     "--desc", "Flux bleus"]) == 0
    capsys.readouterr()
    assert cl._main(["search", "flux"]) == 0
    out = capsys.readouterr().out
    assert "flux-bleus" in out


def test_cli_ingest_glob(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    monkeypatch.setattr(cl, "DEFAULT_ROOT", tmp_path / "lib")
    src = tmp_path / "src"
    src.mkdir()
    for name in ("a.mp4", "b.mp4"):
        (src / name).write_bytes(b"X")
    rc = cl._main(["ingest", str(src / "*.mp4"), "--tags", "abstrait-corporate"])
    assert rc == 0
    assert len(cl.load_index(tmp_path / "lib")["clips"]) == 2


def test_cli_ingest_no_match_returns_1(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cl, "DEFAULT_ROOT", tmp_path / "lib")
    rc = cl._main(["ingest", str(tmp_path / "none-*.mp4"), "--tags", "x"])
    assert rc == 1


def test_cli_show_unknown_returns_1(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cl, "DEFAULT_ROOT", tmp_path / "lib")
    rc = cl._main(["show", "inconnu"])
    assert rc == 1
