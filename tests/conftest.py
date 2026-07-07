import gzip
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    def _load(name: str) -> str:
        with gzip.open(FIXTURES / name, "rt", encoding="utf-8") as f:
            return f.read()

    return _load
