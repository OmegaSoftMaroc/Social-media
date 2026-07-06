import pytest

from pipeline.heygen import build_video_payload, parse_video_status


def test_build_video_payload_linkedin():
    p = build_video_payload("asset42", "avatarX", "linkedin")
    inp = p["video_inputs"][0]
    assert inp["character"] == {"type": "avatar", "avatar_id": "avatarX",
                                "avatar_style": "normal"}
    assert inp["voice"] == {"type": "audio", "audio_asset_id": "asset42"}
    assert p["dimension"] == {"width": 1280, "height": 720}


def test_build_video_payload_short_is_vertical():
    p = build_video_payload("a", "b", "short")
    assert p["dimension"] == {"width": 720, "height": 1280}


def test_build_video_payload_rejects_unknown_format():
    with pytest.raises(KeyError):
        build_video_payload("a", "b", "tiktok-4k")


def test_parse_video_status_completed():
    status, info = parse_video_status(
        {"data": {"status": "completed", "video_url": "https://x/v.mp4"}})
    assert status == "completed" and info == "https://x/v.mp4"


def test_parse_video_status_failed_with_error():
    status, info = parse_video_status(
        {"data": {"status": "failed", "error": {"message": "bad avatar"}}})
    assert status == "failed" and "bad avatar" in info


def test_parse_video_status_processing():
    status, info = parse_video_status({"data": {"status": "processing"}})
    assert status == "processing" and info is None
