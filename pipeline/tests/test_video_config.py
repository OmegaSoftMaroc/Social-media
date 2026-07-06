from pipeline.config import VIDEO_FORMATS, VIDEO_POLL_S, VIDEO_TIMEOUT_S


def test_video_formats_shape():
    assert set(VIDEO_FORMATS) == {"linkedin", "short"}
    for fmt in VIDEO_FORMATS.values():
        assert {"width", "height"} <= set(fmt["dimension"])
        lo, hi = fmt["target_words"]
        assert 0 < lo < hi


def test_short_is_vertical():
    d = VIDEO_FORMATS["short"]["dimension"]
    assert d["height"] > d["width"]


def test_polling_bounds():
    assert VIDEO_POLL_S >= 10
    assert VIDEO_TIMEOUT_S >= 600
