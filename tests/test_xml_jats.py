import pytest
from lxml import etree

from dags.libero.xml.jats import get_article_id


@pytest.mark.parametrize('xml_string', [
    ('<article>'
     '  <front>'
     '      <article-meta>'
     '          <article-id pub-id-type="publisher-id">00666</article-id>'
     '      </article-meta>'
     '  </front>'
     '</article>'),
    ('<article>' 
     '  <front>'
     '      <article-meta>'
     '          <article-id pub-id-type="manuscript">00666</article-id>'
     '      </article-meta>'
     '  </front>'
     '</article>'),
    ('<article>'
     '  <front>'
     '      <article-meta>'
     '          <elocation-id>00666</elocation-id>'
     '      </article-meta>'
     '  </front>'
     '</article>'),
    ('<article>'
     '  <front>'
     '      <article-meta>'
     '          <article-id pub-id-type="doi">00666</article-id>'
     '      </article-meta>'
     '  </front>'
     '</article>'),
    ('<article>'
     '  <front>'
     '      <article-meta>'
     '          <article-id pub-id-type="publisher-id">00666</article-id>'
     '          <article-id pub-id-type="manuscript">00666</article-id>'
     '          <elocation-id>00666</elocation-id>'
     '          <article-id pub-id-type="doi">00666</article-id>'
     '      </article-meta>'
     '  </front>'
     '</article>'),
])
def test_get_article_id(xml_string):
    xml = etree.XML(xml_string)
    assert get_article_id(xml) == '00666'
