from pathlib import Path


def get_asset(name: str) -> Path:
    try:
        path = next(Path('.').rglob(name))
    except StopIteration:
        raise FileNotFoundError
    return path
