from typing import Iterable, List
from xml.dom import XML_NAMESPACE

from lxml.etree import ElementTree


# namespaces
XLINK_NS = 'http://www.w3.org/1999/xlink'

# namespace_maps
XLINK_MAP = {'xlink': XLINK_NS}

# clark notation
# reference: http://www.jclark.com/xml/xmlns.htm
XLINK_HREF = '{%s}href' % XLINK_NS
XML_BASE = '{%s}base' % XML_NAMESPACE


def get_element_text_from_xpaths(xml: ElementTree, xpaths: Iterable[str], namespaces: dict = None) -> List[str]:
    """
    Searches an lxml ElementTree object for all elements xpaths
    and returns a list of text from each element found.
    """
    elements_text = []
    for xpath in xpaths:
        results = xml.xpath(xpath, namespaces=namespaces)
        # get text from element or from all child elements
        results = [e.text.strip()
                   if e.text is not None else e.xpath('string()').strip()
                   for e in results]
        elements_text.extend([r for r in results if r])

    assert elements_text, 'XPaths not found in xml: %s' % str(xpaths)
    return elements_text
