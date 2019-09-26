from typing import List

from lxml.etree import ElementTree

from libero.xml import get_element_text_from_xpaths
from libero.xml.jats import xpaths


# namespaces
JATS_NS = 'http://jats.nlm.nih.gov'

# namespace maps
JATS_MAP = {'jats': JATS_NS}  # for use with libero xml documents only


def get_article_id(jats_xml: ElementTree) -> str:

    strategies = (xpaths.ARTICLE_ID_BY_PUBLISHER_ID,
                  xpaths.ARTICLE_ID_NOT_BY_PMID_PMC_DOI,
                  xpaths.ARTICLE_ID_BY_ELOCATION_ID,
                  xpaths.ARTICLE_ID_BY_DOI)

    return get_element_text_from_xpaths(jats_xml, strategies)[0]


def get_categories(jats_xml: ElementTree) -> List[str]:

    strategies = (xpaths.CATEGORIES_BY_SUBJECT_GROUP,)

    return get_element_text_from_xpaths(jats_xml, strategies)
