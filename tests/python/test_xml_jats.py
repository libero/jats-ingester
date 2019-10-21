import pytest
from lxml import etree

from dags.libero.xml.jats import get_article_id, get_categories


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


def test_get_article_id_raises_exception_when_id_not_found():
    xml = etree.XML('<article><front><article-meta></article-meta></front></article>')
    with pytest.raises(AssertionError):
        get_article_id(xml)


@pytest.mark.parametrize('xml_string, expected', [
    ('<article>'
     '  <front>'
     '    <article-meta>'
     '      <article-categories>'
     '        <subj-group subj-group-type="heading">'
     '          <subject>Research Article</subject>'
     '        </subj-group>'
     '        <subj-group subj-group-type="subjects">'
     '          <subject>Cancer Biology</subject>'
     '        </subj-group>'
     '      </article-categories>'
     '    </article-meta>'
     '  </front>'
     '</article>',
     ['Cancer Biology']),
    ('<article>'
     '  <front>'
     '    <article-meta>'
     '      <article-categories>'
     '        <subj-group subj-group-type="heading">'
     '          <subject>Research Article</subject>'
     '        </subj-group>'
     '        <subj-group subj-group-type="subjects">'
     '          <subject>Cancer Biology</subject>'
     '          <subject>General Economics</subject>'
     '        </subj-group>'
     '      </article-categories>'
     '    </article-meta>'
     '  </front>'
     '</article>',
     ['Cancer Biology']),
    ('<article>'
     '  <front>'
     '    <article-meta>'
     '      <article-categories>'
     '        <subj-group subj-group-type="heading">'
     '          <subject>Research Article</subject>'
     '        </subj-group>'
     '        <subj-group>'
     '          <subject>General Economics</subject>'
     '          <subject>Cancer Biology</subject>'
     '        </subj-group>'
     '      </article-categories>'
     '    </article-meta>'
     '  </front>'
     '</article>',
     ['General Economics']),
    ('<article>'
     '  <front>'
     '    <article-meta>'
     '      <article-categories>'
     '        <subj-group subj-group-type="heading">'
     '          <subject>Research Article</subject>'
     '        </subj-group>'
     '        <subj-group subj-group-type="subjects">'
     '          <subject>Cancer Biology</subject>'
     '        </subj-group>'
     '        <subj-group subj-group-type="subjects">'
     '          <subject>General Economics</subject>'
     '        </subj-group>'
     '      </article-categories>'
     '    </article-meta>'
     '  </front>'
     '</article>',
     ['Cancer Biology', 'General Economics']),
    ('<article>'
     '  <front>'
     '    <article-meta>'
     '      <article-categories>'
     '        <subj-group subj-group-type="heading">'
     '          <subject>Research Article</subject>'
     '        </subj-group>'
     '        <subj-group subj-group-type="subjects">'
     '          <subject>Cancer Biology</subject>'
     '        </subj-group>'
     '        <subj-group>'
     '          <subject>General Economics</subject>'
     '        </subj-group>'
     '      </article-categories>'
     '    </article-meta>'
     '  </front>'
     '</article>',
     ['Cancer Biology', 'General Economics']),
    ('<article>'
     '  <front>'
     '    <article-meta>'
     '      <article-categories>'
     '        <subj-group subj-group-type="heading">'
     '          <subject>Research Article</subject>'
     '        </subj-group>'
     '        <subj-group subj-group-type="subjects">'
     '          <subject>Cancer Biology</subject>'
     '        </subj-group>'
     '        <subj-group>'
     '          <subject>Data</subject>'
     '        </subj-group>'
     '        <subj-group subj-group-type="subjects">'
     '          <subject>Housing</subject>'
     '        </subj-group>'
     '        <subj-group>'
     '          <subject>General Economics</subject>'
     '        </subj-group>'
     '      </article-categories>'
     '    </article-meta>'
     '  </front>'
     '</article>',
     ['Cancer Biology', 'Data', 'Housing', 'General Economics']),
    ('<article>'
     '  <front>'
     '    <article-meta>'
     '      <article-categories>'
     '        <subj-group subj-group-type="heading">'
     '          <subject>Research Article</subject>'
     '        </subj-group>'
     '        <subj-group subj-group-type="subjects">'
     '          <subject></subject>'
     '        </subj-group>'
     '        <subj-group>'
     '          <subject>Data</subject>'
     '        </subj-group>'
     '        <subj-group subj-group-type="subjects">'
     '          <subject>Housing</subject>'
     '        </subj-group>'
     '        <subj-group>'
     '          <subject>General Economics</subject>'
     '        </subj-group>'
     '      </article-categories>'
     '    </article-meta>'
     '  </front>'
     '</article>',
     ['Data', 'Housing', 'General Economics']),
    ('<article xmlns:mml="http://www.w3.org/1998/Math/MathML">'
     '  <front>'
     '    <article-meta>'
     '      <article-categories>'
     '        <subj-group subj-group-type="heading">'
     '          <subject>Research Article</subject>'
     '        </subj-group>'
     '        <subj-group subj-group-type="subjects">'
     '          <subject><italic>Cancer Biology</italic></subject>'
     '        </subj-group>'
     '        <subj-group>'
     '          <subject>Data</subject>'
     '          <subj-group subj-group-type="subjects">'
     '            <subject>Housing</subject>'
     '            <subj-group>'
     '              <subject>General Economics</subject>'
     '            </subj-group>'
     '          </subj-group>'
     '        </subj-group>'
     '        <subj-group subj-group-type="level-1">'
     '          <subject>Ecology</subject>'
     '          <subject>Genetics and Genomics</subject>'
     '          <subj-group subj-group-type="level-2">'
     '            <subject>Evolutionary Biology</subject>'
     '            <subj-group subj-group-type="level-3">'
     '              <subject>General Economics</subject>'
     '              <subject><bold>Plant Biology</bold></subject>'
     '            </subj-group>'
     '          </subj-group>'
     '        </subj-group>'
     '        <subj-group subj-group-type="any-value">'
     '          <subject><mml:math id="i1" display="inline"><mml:mover accent="true"><mml:mi>α</mml:mi><mml:mo>^</mml:mo></mml:mover></mml:math></subject>'
     '          <subj-group subj-group-type="nested-sub">'
     '            <subject><mml:math id="i2" display="inline"><mml:mover accent="true"><mml:mi>β</mml:mi><mml:mo>^</mml:mo></mml:mover></mml:math></subject>'
     '          </subj-group>'
     '        </subj-group>'
     '      </article-categories>'
     '    </article-meta>'
     '  </front>'
     '</article>',
     ['Cancer Biology', 'Data', 'Ecology', 'α^']),
])
def test_get_categories(xml_string, expected):
    xml = etree.XML(xml_string)
    assert get_categories(xml) == expected


def test_get_categories_raises_exception_when_categories_not_found():
    xml_string = (
        '<article>'
        '  <front>'
        '    <article-meta>'
        '      <article-categories>'
        '        <subj-group subj-group-type="heading">'
        '          <subject>Research Article</subject>'
        '        </subj-group>'
        '      </article-categories>'
        '    </article-meta>'
        '  </front>'
        '</article>'
    )
    xml = etree.XML(xml_string)
    with pytest.raises(AssertionError):
        get_categories(xml)
