from pathlib import Path
from typing import List


def get_asset(name: str) -> Path:
    try:
        path = next(Path(__file__).parent.rglob(name))
    except StopIteration:
        raise FileNotFoundError(name)
    return path


def find_asset(name: str) -> List[Path]:
    paths = list(Path(__file__).parent.rglob(name))
    if not paths:
        raise FileNotFoundError(name)
    return paths
