import json
from pathlib import Path
import pytest


@pytest.fixture
def briefs_dir(tmp_path: Path) -> Path:
    """Arborescence briefs/ isolée pour les tests."""
    for sub in ("incoming", "processed", "proposals"):
        (tmp_path / sub).mkdir(parents=True)
    return tmp_path


def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
