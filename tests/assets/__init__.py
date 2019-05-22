from pathlib import Path


def get_asset(name):
    try:
        path = next(Path('.').glob('**/%s' % name))
    except StopIteration:
        raise FileNotFoundError
    return path.read_bytes()
