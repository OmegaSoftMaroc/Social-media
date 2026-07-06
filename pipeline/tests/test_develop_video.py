import json
from pathlib import Path

import pipeline.develop_video as dv


def test_artifact_paths(tmp_path):
    paths = dv.artifact_paths(tmp_path, "idee3")
    assert paths["script"] == tmp_path / "briefs" / "output" / "idee3" / "video-script.json"
    assert paths["audio"].name == "audio.mp3"
    assert paths["video"].name == "video.mp4"


def test_render_video_notification():
    msg = dv.render_video_notification(
        {"titre": "Agents IA", "duree_estimee_s": 40, "format": "short",
         "script": "abc def"},
        "https://drive/x")
    assert "Agents IA" in msg
    assert "short" in msg
    assert "https://drive/x" in msg
    assert "publie la vidéo" in msg.lower()


def test_main_skips_existing_artifacts(tmp_path, monkeypatch):
    # Prépare une idée + artefacts déjà présents (script + audio)
    proposals = tmp_path / "briefs" / "proposals"
    proposals.mkdir(parents=True)
    (proposals / "latest.json").write_text(json.dumps(
        {"idees": [{"id": "idee-1", "pilier": 1, "titre": "T", "angle": "A"}]}),
        encoding="utf-8")
    paths = dv.artifact_paths(tmp_path, "idee1")
    paths["script"].parent.mkdir(parents=True)
    paths["script"].write_text(json.dumps(
        {"format": "short", "script": "s", "titre": "T", "description": "d"}),
        encoding="utf-8")
    paths["audio"].write_bytes(b"mp3")

    calls = {"script": 0, "tts": 0, "video": 0}
    monkeypatch.setattr(dv, "call_scriptwriter",
                        lambda *a, **k: calls.__setitem__("script", 1) or {})
    monkeypatch.setattr(dv, "make_audio",
                        lambda *a, **k: calls.__setitem__("tts", 1))
    monkeypatch.setattr(dv, "make_video",
                        lambda script, audio, out, fmt: calls.__setitem__("video", 1)
                        or Path(out).write_bytes(b"v"))
    monkeypatch.setattr(dv, "upload_to_drive", lambda p, name: "https://drive/ok")
    monkeypatch.setattr(dv, "send_telegram", lambda t: None)

    assert dv.main(1, "short", base=tmp_path) == 0
    assert calls == {"script": 0, "tts": 0, "video": 1}  # script+audio réutilisés
