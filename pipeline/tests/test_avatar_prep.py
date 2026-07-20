from pathlib import Path

import pipeline.avatar_prep as ap


def test_build_words_groups_chars_into_words():
    """L'alignement caractère est regroupé en mots avec bornes ms correctes."""
    chars = list("le bon mot")
    starts = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    ends = [s + 0.1 for s in starts]
    words = ap.build_words(chars, starts, ends)
    assert [w["text"] for w in words] == ["le", "bon", "mot"]
    assert words[0] == {"text": "le", "startMs": 0, "endMs": 200}
    assert words[1]["startMs"] == 300 and words[1]["endMs"] == 600
    assert words[2]["startMs"] == 700 and words[2]["endMs"] == 1000


def test_build_words_ignores_leading_trailing_spaces():
    """Espaces multiples/terminaux : pas de mots vides."""
    chars = list(" a  b ")
    starts = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    ends = [s + 0.1 for s in starts]
    words = ap.build_words(chars, starts, ends)
    assert [w["text"] for w in words] == ["a", "b"]


def test_measure_bounds_finds_content_between_white_bars(tmp_path: Path):
    """Bandes blanches latérales détectées : le contenu est borné correctement."""
    from PIL import Image

    im = Image.new("RGB", (200, 100), "white")
    for x in range(60, 140):  # bande de contenu sombre au centre
        for y in range(100):
            im.putpixel((x, y), (20, 30, 40))
    p = tmp_path / "frame.png"
    im.save(p)
    x0, x1 = ap.measure_bounds(p)
    assert 52 <= x0 <= 64
    assert 136 <= x1 <= 148
