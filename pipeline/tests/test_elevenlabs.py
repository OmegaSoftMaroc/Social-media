from pipeline.elevenlabs import build_tts_payload, tts_url


def test_build_tts_payload():
    p = build_tts_payload("Bonjour, parlons agents IA.")
    assert p["text"] == "Bonjour, parlons agents IA."
    assert p["model_id"] == "eleven_multilingual_v2"
    assert 0 <= p["voice_settings"]["stability"] <= 1


def test_tts_url_injects_voice_id():
    assert tts_url("abc123").endswith("/text-to-speech/abc123")
