import pytest

from tests.assets import get_asset


@pytest.mark.parametrize('asset_name', ['elife-666.xml', 'elife-666-vor-r1.zip'])
def test_get_assets(asset_name):
    assert get_asset(asset_name)


def test_get_assets_raises_exception():
    with pytest.raises(FileNotFoundError):
        get_asset('does-not-exist.txt')
