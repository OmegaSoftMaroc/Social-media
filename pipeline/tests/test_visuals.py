from pipeline.visuals import build_visual_prompt


def test_build_visual_prompt_includes_title_and_format():
    p = build_visual_prompt({"titre": "Agent IA pour PME"})
    assert "Agent IA pour PME" in p
    assert "4x5" in p
    assert "filigrane" in p.lower()


def test_build_visual_prompt_handles_missing_title():
    p = build_visual_prompt({})
    assert isinstance(p, str) and len(p) > 0
