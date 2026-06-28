from datetime import datetime, timezone, timedelta
from pathlib import Path
import json

from pipeline.youtube_monitor import (
    is_recent,
    select_new_videos,
    make_incoming_item,
    write_incoming_item,
)


def _rfc822(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def test_is_recent_true_for_now():
    now = datetime.now(timezone.utc)
    assert is_recent(_rfc822(now), hours=25) is True


def test_is_recent_false_for_old():
    old = datetime.now(timezone.utc) - timedelta(hours=48)
    assert is_recent(_rfc822(old), hours=25) is False


def test_select_new_videos_filters_seen_and_old():
    now = datetime.now(timezone.utc)
    videos = [
        {"id": "v1", "titre": "A", "url": "u1", "description": "d", "publie_le": _rfc822(now)},
        {"id": "v2", "titre": "B", "url": "u2", "description": "d", "publie_le": _rfc822(now)},
        {"id": "v3", "titre": "C", "url": "u3", "description": "d",
         "publie_le": _rfc822(now - timedelta(hours=48))},
    ]
    seen = {"v1": {}}
    result = select_new_videos(videos, seen, hours=25)
    ids = [v["id"] for v in result]
    assert ids == ["v2"]  # v1 déjà vu, v3 trop ancien


def test_make_incoming_item_shape():
    video = {"id": "v9", "titre": "T", "url": "https://youtu.be/v9",
             "description": "desc", "publie_le": "Sat, 28 Jun 2026 07:00:00 +0000"}
    item = make_incoming_item(video, chaine="@nateherk", resume_fr="résumé",
                              detecte_le="2026-06-28T07:30:00")
    assert item == {
        "source": "youtube",
        "video_id": "v9",
        "chaine": "@nateherk",
        "titre": "T",
        "url": "https://youtu.be/v9",
        "publie_le": "Sat, 28 Jun 2026 07:00:00 +0000",
        "resume_fr": "résumé",
        "detecte_le": "2026-06-28T07:30:00",
    }


def test_write_incoming_item_creates_file(briefs_dir: Path):
    item = {"video_id": "v9", "titre": "T"}
    path = write_incoming_item(item, briefs_dir / "incoming")
    assert path.name == "v9.json"
    assert json.loads(path.read_text(encoding="utf-8"))["titre"] == "T"
