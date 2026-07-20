import json
from pathlib import Path

import pipeline.orchestrator as orch


def test_main_writes_proposals_and_archives(briefs_dir: Path, monkeypatch):
    # une opportunité en file
    (briefs_dir / "incoming" / "v1.json").write_text(
        json.dumps({"video_id": "v1", "titre": "T", "url": "u", "chaine": "@x"}),
        encoding="utf-8")

    # curator mocké → renvoie 1 idée
    def fake_curator(workspace, items):
        return {"date": "2026-06-28",
                "idees": [{"id": "idee-1", "pilier": 1, "titre": "T",
                           "source": {"type": "youtube", "url": "u"}}],
                "recommandation": {"id": "idee-1", "pourquoi": "ok"}}

    sent = {}
    def fake_send(text):
        sent["text"] = text

    monkeypatch.setattr(orch, "call_curator", fake_curator)
    monkeypatch.setattr(orch, "send_telegram", fake_send)

    n = orch.main(base=briefs_dir.parent, workspace="/unused", date="2026-06-28",
                  briefs_root=briefs_dir)

    assert n == 1
    assert "1." in sent["text"]
    assert (briefs_dir / "proposals" / "latest.json").exists()
    # l'item a été archivé
    assert (briefs_dir / "processed" / "v1.json").exists()
    assert not (briefs_dir / "incoming" / "v1.json").exists()


def test_main_no_incoming_skips_send(briefs_dir: Path, monkeypatch):
    called = {"send": False}
    monkeypatch.setattr(orch, "call_curator", lambda *a, **k: {"idees": []})
    monkeypatch.setattr(orch, "send_telegram",
                        lambda text: called.__setitem__("send", True))
    n = orch.main(base=briefs_dir.parent, workspace="/unused", date="2026-06-28",
                  briefs_root=briefs_dir)
    assert n == 0
    assert called["send"] is False  # rien à envoyer si file vide
