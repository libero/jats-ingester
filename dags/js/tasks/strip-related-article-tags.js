const jatsXpaths = require('../xml/jats-xpaths');
const stripTag = require('../xml/strip-tag');


function stripRelatedArticleTags(xmlStringBuffer) {
  let xmlDocAsString = stripTag(xmlStringBuffer.toString(), jatsXpaths.RELATED_ARTICLE);
  return Buffer.from(xmlDocAsString);
}

module.exports = stripRelatedArticleTags;
