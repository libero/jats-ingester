const jatsXpaths = require('./jats-xpaths');
const libxmljs = require('libxmljs');


function stripRelatedArticleTags(xmlStringBuffer) {

  let xmlDoc = libxmljs.parseXml(xmlStringBuffer.toString());

  xmlDoc.find(jatsXpaths.RELATED_ARTICLE).forEach((element) => {
    element.remove();
  });

  // adding false to document.toString should remove formatting but
  // a few newlines (\n) can still be found
  let xmlDocAsString = xmlDoc.toString(false);

  // actually remove formatting
  return Buffer.from(xmlDocAsString.replace(new RegExp('\n', 'g'), ''));
}

module.exports = stripRelatedArticleTags;
