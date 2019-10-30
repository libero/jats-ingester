const libxmljs = require('libxmljs');
const jatsXpaths = require('../xml/jats-xpaths');


function addMissingJPEGExtensionsInArticle(xmlStringBuffer) {

  let xmlDoc = libxmljs.parseXml(xmlStringBuffer.toString());

  xmlDoc.find(jatsXpaths.IMAGE_BY_JPEG_MIMETYPE).forEach((element) => {

    for (let attribute of element.attrs()) {

      try {
        var prefix = attribute.namespace().prefix();
      } catch(error) {
        continue;
      }

      if (prefix === 'xlink' &&
          attribute.name() === 'href' &&
          attribute.value().endsWith('.jpg') === false) {

        attribute.value(attribute.value() + '.jpg');
        break;
      }

    }

  });

  // adding false to document.toString should remove formatting but
  // a few newlines (\n) can still be found
  let xmlDocAsString = xmlDoc.toString(false);

  // actually remove formatting
  xmlDocAsString = xmlDocAsString.replace(new RegExp('\n', 'g'), '');

  return Buffer.from(xmlDocAsString);
}

module.exports = addMissingJPEGExtensionsInArticle;
