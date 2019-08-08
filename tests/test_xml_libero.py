from lxml import etree

from dags.libero.xml.libero import get_content_id
from tests.assets import get_asset


def test_get_content_id():
    test_asset_path = str(get_asset('libero-00666.xml').absolute())
    article_xml = etree.parse(test_asset_path)
    assert get_content_id(article_xml) == '00666'