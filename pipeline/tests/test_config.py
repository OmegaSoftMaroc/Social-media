from pipeline.config import CHANNELS, KNOWN_IDS, IDEAS_PER_RUN


def test_channels_have_known_ids():
    for handle in CHANNELS:
        assert handle in KNOWN_IDS and KNOWN_IDS[handle], f"id manquant pour {handle}"


def test_ideas_per_run_range():
    assert IDEAS_PER_RUN == (3, 5)
