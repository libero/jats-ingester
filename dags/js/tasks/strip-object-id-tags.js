const jatsXpaths = require('../xml/jats-xpaths');
const stripTag = require('../xml/strip-tag');


function stripObjectIDTags(xmlStringBuffer) {
  let xmlDocAsString = stripTag(xmlStringBuffer.toString(), jatsXpaths.OBJECT_ID);
  return Buffer.from(xmlDocAsString);
}

module.exports = stripObjectIDTags;
