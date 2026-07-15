from pathlib import Path

import pytest

import pipeline.animate as an
import pipeline.clip_library as cl


def test_reuse_tags_skips_fal(tmp_path, monkeypatch):
    """Un clip taggé présent sur disque est réutilisé sans aucun appel fal."""
    root = tmp_path / "lib"
    src = tmp_path / "src.mp4"
    src.write_bytes(b"CLIPBYTES")
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    monkeypatch.setattr(cl, "DEFAULT_ROOT", root)
    cl.add_clip(root, src, ["flux-donnees", "bleu"], "Flux bleus",
                clip_id="ok", cost_usd=0.35)

    def _boom(*a, **k):
        raise AssertionError("fal ne doit PAS être appelé quand un clip est réutilisé")
    monkeypatch.setattr(an.requests, "post", _boom)

    out = tmp_path / "out.mp4"
    result = an.animate_image(tmp_path / "still.png", out,
                              reuse_tags=["flux-donnees"])
    assert Path(result) == out
    assert out.read_bytes() == b"CLIPBYTES"


def test_no_reuse_tags_still_calls_fal(tmp_path, monkeypatch):
    """Sans reuse_tags, le comportement fal historique est conservé (post appelé)."""
    monkeypatch.setenv("FAL_KEY", "k")
    called = {"post": False}

    def _fake_post(*a, **k):
        called["post"] = True
        raise RuntimeError("stop après soumission")

    monkeypatch.setattr(an.requests, "post", _fake_post)
    (tmp_path / "still.png").write_bytes(b"\x89PNG\r\n")
    with pytest.raises(RuntimeError):
        an.animate_image(tmp_path / "still.png", tmp_path / "o.mp4")
    assert called["post"] is True


def test_reuse_tags_falls_back_to_fal_when_clip_file_missing(tmp_path, monkeypatch):
    """Binaire catalogué purgé (MP4 non versionnés) → génération fal, pas de crash."""
    root = tmp_path / "lib"
    src = tmp_path / "src.mp4"
    src.write_bytes(b"CLIPBYTES")
    monkeypatch.setattr(cl, "make_thumb", lambda *a, **k: False)
    monkeypatch.setattr(cl, "DEFAULT_ROOT", root)
    entry = cl.add_clip(root, src, ["flux-donnees"], "Flux", clip_id="gone")
    (root / entry["file"]).unlink()  # binaire purgé, index conservé
    monkeypatch.setenv("FAL_KEY", "k")
    called = {"post": False}

    def _fake_post(*a, **k):
        called["post"] = True
        raise RuntimeError("stop après soumission")

    monkeypatch.setattr(an.requests, "post", _fake_post)
    (tmp_path / "still.png").write_bytes(b"\x89PNG\r\n")
    with pytest.raises(RuntimeError):
        an.animate_image(tmp_path / "still.png", tmp_path / "o.mp4",
                         reuse_tags=["flux-donnees"])
    assert called["post"] is True


def test_cli_parses_reuse_tags(tmp_path, monkeypatch):
    """--reuse-tags a,b est bien découpé en liste et transmis à animate_image."""
    captured = {}

    def _fake_animate(image_path, out_path, **kwargs):
        captured.update(kwargs)
        Path(out_path).write_bytes(b"X")
        return out_path

    monkeypatch.setattr(an, "animate_image", _fake_animate)
    rc = an._main([str(tmp_path / "img.png"), str(tmp_path / "o.mp4"),
                   "--reuse-tags", "flux-donnees,bleu"])
    assert rc == 0
    assert captured["reuse_tags"] == ["flux-donnees", "bleu"]
