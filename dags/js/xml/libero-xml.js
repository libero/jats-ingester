const liberoXpaths = require('./libero-xpaths');
const namespaces = require('./namespaces');


module.exports.getContentID = function(liberoXmlDoc) {
  let results = liberoXmlDoc.find(liberoXpaths.ID, {'libero': namespaces.LIBERO});
  if (results.length > 0) {
    return results[0].text()
  }
  throw new Error('Unable to find content ID')
};
