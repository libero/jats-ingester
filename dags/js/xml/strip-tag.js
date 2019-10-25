const libxmljs = require('libxmljs');


function stripTag(xmlString, tagXpath) {

  let xmlDoc = libxmljs.parseXml(xmlString);

  xmlDoc.find(tagXpath).forEach((element) => {
    element.remove();
  });

  // adding false to document.toString should remove formatting but
  // a few newlines (\n) can still be found
  let xmlDocAsString = xmlDoc.toString(false);

  // actually remove formatting
  return xmlDocAsString.replace(new RegExp('\n', 'g'), '')
}

module.exports = stripTag;
