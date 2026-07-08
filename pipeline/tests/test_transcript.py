"""Tests du connecteur transcript (récupération YouTube via Webshare)."""
import pytest

from pipeline import transcript


class _FakeSnippet:
    def __init__(self, start, text):
        self.start = start
        self.text = text


class _FakeFetched:
    """Imite FetchedTranscript : itérable de snippets + language_code."""
    language_code = "en"

    def __init__(self, snippets):
        self._snippets = snippets

    def __iter__(self):
        return iter(self._snippets)


# --- extract_video_id ---------------------------------------------------------

@pytest.mark.parametrize("value,expected", [
    ("https://youtu.be/XTBWVVcF3Pk?si=19HLw7XJmL9qQ3ya", "XTBWVVcF3Pk"),
    ("https://www.youtube.com/watch?v=XTBWVVcF3Pk&t=42s", "XTBWVVcF3Pk"),
    ("https://www.youtube.com/shorts/XTBWVVcF3Pk", "XTBWVVcF3Pk"),
    ("XTBWVVcF3Pk", "XTBWVVcF3Pk"),
])
def test_extract_video_id_forms(value, expected):
    assert transcript.extract_video_id(value) == expected


def test_extract_video_id_rejette_invalide():
    with pytest.raises(ValueError):
        transcript.extract_video_id("https://example.com/pas-une-video")


# --- _webshare_config ---------------------------------------------------------

def test_webshare_config_present_quand_credentials():
    cfg = transcript._webshare_config(
        {"WEBSHARE_PROXY_USERNAME": "u", "WEBSHARE_PROXY_PASSWORD": "p"})
    assert cfg is not None


def test_webshare_config_absent_sans_credentials():
    assert transcript._webshare_config({}) is None


# --- fetch_transcript ---------------------------------------------------------

def test_fetch_transcript_assemble_texte_et_segments(monkeypatch):
    captured = {}

    class _FakeApi:
        def __init__(self, proxy_config=None):
            captured["proxy_config"] = proxy_config

        def fetch(self, video_id, languages=None):
            captured["video_id"] = video_id
            captured["languages"] = languages
            return _FakeFetched([
                _FakeSnippet(0.0, "Hello\nworld"),
                _FakeSnippet(2.5, "  second line  "),
            ])

    monkeypatch.setattr(transcript, "YouTubeTranscriptApi", _FakeApi)

    result = transcript.fetch_transcript(
        "https://youtu.be/XTBWVVcF3Pk", env={})

    assert result["video_id"] == "XTBWVVcF3Pk"
    assert result["language"] == "en"
    assert result["text"] == "Hello world second line"
    assert result["segments"][0] == {"start": 0.0, "text": "Hello world"}
    assert captured["proxy_config"] is None  # pas de credentials -> direct


def test_fetch_transcript_utilise_proxy_quand_credentials(monkeypatch):
    captured = {}

    class _FakeApi:
        def __init__(self, proxy_config=None):
            captured["proxy_config"] = proxy_config

        def fetch(self, video_id, languages=None):
            return _FakeFetched([_FakeSnippet(0.0, "ok")])

    monkeypatch.setattr(transcript, "YouTubeTranscriptApi", _FakeApi)

    transcript.fetch_transcript(
        "XTBWVVcF3Pk",
        env={"WEBSHARE_PROXY_USERNAME": "u", "WEBSHARE_PROXY_PASSWORD": "p"})

    assert captured["proxy_config"] is not None  # proxy Webshare injecté
