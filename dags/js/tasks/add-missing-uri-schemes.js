const libxmljs = require('libxmljs');
const namespaces = require('../xml/namespaces');
const xpaths = require('../xml/xpaths');


function addMissingURIScheme(xmlStringBuffer) {

  let xmlDoc = libxmljs.parseXml(xmlStringBuffer.toString());

  xmlDoc.find(xpaths.XLINK_HREF_STARTS_WITH_WWW, {'xlink': namespaces.XLINK}).forEach((element) => {

    for (let attribute of element.attrs()) {

      try {
        var prefix = attribute.namespace().prefix();
      } catch(error) {
        continue;
      }

      if (prefix === 'xlink' && attribute.name() === 'href') {
        attribute.value('http://' + attribute.value());
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

module.exports = addMissingURIScheme;
