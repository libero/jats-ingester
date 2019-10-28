const jatsXpaths = require(process.env.AIRFLOW_HOME + '/dags/js/xml/jats-xpaths');
const stripTag = require(process.env.AIRFLOW_HOME + '/dags/js/xml/strip-tag.js');

test('strips specified tag from xml', () => {
  let xmlStringWithRelatedArticleTag = '<?xml version="1.0" encoding="UTF-8"?>' +
                                       '<article>' +
                                         '<front>' +
                                           '<article-meta>' +
                                             '<related-article/>' +
                                           '</article-meta>' +
                                         '</front>' +
                                       '</article>';

  let xmlStringWithoutRelatedArticleTag = '<?xml version="1.0" encoding="UTF-8"?>' +
                                          '<article>' +
                                            '<front>' +
                                              '<article-meta/>' +
                                            '</front>' +
                                          '</article>';

  let result = stripTag(xmlStringWithRelatedArticleTag, jatsXpaths.RELATED_ARTICLE);
  expect(result).toBe(xmlStringWithoutRelatedArticleTag);

  result = stripTag(xmlStringWithoutRelatedArticleTag, jatsXpaths.RELATED_ARTICLE);
  expect(result).toBe(xmlStringWithoutRelatedArticleTag);
});
