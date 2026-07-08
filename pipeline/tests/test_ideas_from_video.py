"""Tests de ideas_from_video : construction de l'item grounded transcript."""
from pipeline import ideas_from_video


def test_build_item_grounded_sur_transcript(monkeypatch):
    monkeypatch.setattr(ideas_from_video, "fetch_transcript", lambda u: {
        "video_id": "XTBWVVcF3Pk", "language": "en",
        "text": "mot " * 10, "segments": []})
    monkeypatch.setattr(ideas_from_video, "_oembed",
                        lambda vid: ("Titre Vidéo", "Nate Herk"))

    item = ideas_from_video.build_item("https://youtu.be/XTBWVVcF3Pk")

    assert item["source"] == "youtube"
    assert item["video_id"] == "XTBWVVcF3Pk"
    assert item["chaine"] == "Nate Herk"
    assert item["titre"] == "Titre Vidéo"
    assert item["url"] == "https://youtu.be/XTBWVVcF3Pk"
    assert "mot" in item["transcript"]
    assert item["transcript_tronque"] is False


def test_build_item_tronque_transcript_long(monkeypatch):
    monkeypatch.setattr(ideas_from_video, "fetch_transcript", lambda u: {
        "video_id": "XTBWVVcF3Pk", "language": "en",
        "text": "x" * 9000, "segments": []})
    monkeypatch.setattr(ideas_from_video, "_oembed", lambda vid: ("", ""))

    item = ideas_from_video.build_item("XTBWVVcF3Pk", max_chars=6000)

    assert len(item["transcript"]) == 6000
    assert item["transcript_tronque"] is True
    assert item["titre"] == "XTBWVVcF3Pk"  # fallback sur l'id si oembed vide
