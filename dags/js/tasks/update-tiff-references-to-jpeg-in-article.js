const libxmljs = require('libxmljs');
const jatsXpaths = require('../xml/jats-xpaths');
const namespaces = require('../xml/namespaces');
const xpaths = require('../xml/xpaths');


function updateTiffReferencesToJPEGInArticle(xmlStringBuffer) {

  let xmlDoc = libxmljs.parseXml(xmlStringBuffer.toString());

  xmlDoc.find(jatsXpaths.IMAGE_BY_TIFF_MIMETYPE).forEach((element) => {

    for (let attribute of element.attrs()) {

      try {
        var prefix = attribute.namespace().prefix();
      } catch(error) {
        if (attribute.name() === 'mime-subtype') {
          attribute.value('jpeg');
        }
      }

      if (prefix === 'xlink' && attribute.name() === 'href') {
        attribute.value(attribute.value().replace(new RegExp('\\.\\w+$'), '.jpg'));
      }

    }

  });

  xmlDoc.find(xpaths.XLINK_HREF_CONTAINS_TIF, {'xlink': namespaces.XLINK}).forEach((element) => {

    for (let attribute of element.attrs()) {

      try {
        var prefix = attribute.namespace().prefix();
      } catch(error) {
        continue;
      }

      if (prefix === 'xlink' && attribute.name() === 'href') {
        attribute.value(attribute.value().replace(new RegExp('\\.\\w+$'), '.jpg'));
        break;
      }

    }

  });

  // adding false to document.toString should remove formatting but
  // a few newlines (\n) can still be found
  let xmlDocAsString = xmlDoc.toString(false);

  // actually remove formatting
  return xmlDocAsString.replace(new RegExp('\n', 'g'), '')
}

module.exports = updateTiffReferencesToJPEGInArticle;
