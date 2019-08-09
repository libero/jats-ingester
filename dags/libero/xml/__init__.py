from typing import Iterable
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


def get_element_text_from_xpaths(xml: ElementTree, xpaths: Iterable[str], namespaces: dict = None) -> str:
    """
    Searches an lxml ElementTree object for an element using one or more xpaths
    and returns the text of the first element found.
    """
    text = None
    for xpath in xpaths:
        elements = xml.xpath(xpath, namespaces=namespaces)
        if elements:
            text = elements[0].text
            break
    assert text is not None, 'Xpaths not found in xml: %s' % xpaths
    return text
