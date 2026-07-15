from pathlib import Path

import pytest

import pipeline.animate as an
import pipeline.clip_library as cl


def test_reuse_tags_skips_fal(tmp_path, monkeypatch):
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
