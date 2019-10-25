const jatsXPaths = require('../xml/jats-xpaths');


module.exports.getArticleID = function(jatsXmlDoc) {
  let xpaths = [jatsXPaths.ARTICLE_ID_BY_PUBLISHER_ID,
                jatsXPaths.ARTICLE_ID_NOT_BY_PMID_PMC_DOI,
                jatsXPaths.ARTICLE_ID_BY_ELOCATION_ID,
                jatsXPaths.ARTICLE_ID_BY_DOI];

  for (let xpath of xpaths) {
    let results = jatsXmlDoc.find(xpath);
    if (results.length > 0) {
      return results[0].text()
    }
  }

  throw new Error('Unable to find article ID')
};
