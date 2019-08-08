from lxml.etree import ElementTree

from libero.xml import get_element_text_from_xpaths
from libero.xml.libero import xpaths


# namespaces
LIBERO_NS = 'http://libero.pub'

# namespace maps
LIBERO_MAP = {'libero': LIBERO_NS}


def get_content_id(jats_xml: ElementTree) -> str:
    return get_element_text_from_xpaths(
        xml=jats_xml,
        xpaths=[xpaths.ID],
        namespaces=LIBERO_MAP
    )
