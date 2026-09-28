import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=None)
def load_json(name: str):
    with open(DATA_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def load_text(name: str) -> str:
    return (DATA_DIR / name).read_text(encoding="utf-8")
