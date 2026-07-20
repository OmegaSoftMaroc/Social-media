import json
from pathlib import Path

from pipeline.orchestrator import (
    load_incoming,
    render_proposal_message,
    write_proposals,
    archive_processed,
)


def _write(path: Path, obj: dict):
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def test_load_incoming_reads_all_items(briefs_dir: Path):
    _write(briefs_dir / "incoming" / "a.json", {"video_id": "a", "titre": "A"})
    _write(briefs_dir / "incoming" / "b.json", {"video_id": "b", "titre": "B"})
    items = load_incoming(briefs_dir / "incoming")
    titres = sorted(i["titre"] for i in items)
    assert titres == ["A", "B"]


def test_load_incoming_empty(briefs_dir: Path):
    assert load_incoming(briefs_dir / "incoming") == []


def test_render_proposal_message_numbers_ideas():
    proposals = {"idees": [
        {"id": "idee-1", "pilier": 1, "titre": "Orchestrer des agents"},
        {"id": "idee-2", "pilier": 5, "titre": "Pourquoi les PME marocaines"},
    ], "recommandation": {"id": "idee-1", "pourquoi": "fort sur LinkedIn"}}
    msg = render_proposal_message(proposals)
    assert "1." in msg and "2." in msg
    assert "Orchestrer des agents" in msg
    assert "Pourquoi les PME marocaines" in msg
    assert "recommand" in msg.lower()


def test_render_proposal_message_empty():
    msg = render_proposal_message({"idees": []})
    assert "aucune" in msg.lower()


def test_write_proposals_creates_dated_and_latest(briefs_dir: Path):
    proposals = {"date": "2026-06-28", "idees": [{"id": "idee-1"}]}
    dated, latest = write_proposals(proposals, briefs_dir / "proposals", date="2026-06-28")
    assert dated.name == "2026-06-28.json"
    assert latest.name == "latest.json"
    assert json.loads(latest.read_text(encoding="utf-8"))["date"] == "2026-06-28"


def test_archive_processed_moves_files(briefs_dir: Path):
    src = briefs_dir / "incoming" / "a.json"
    _write(src, {"video_id": "a"})
    archive_processed(["a"], briefs_dir / "incoming", briefs_dir / "processed")
    assert not src.exists()
    assert (briefs_dir / "processed" / "a.json").exists()
