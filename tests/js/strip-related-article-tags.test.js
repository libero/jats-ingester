const stripRelatedArticleTags = require(process.env.AIRFLOW_HOME + '/dags/js/xml/strip-related-article-tags.js');

test('strips <related-article> tags from xml', () => {
  let xmlStringWithRelatedArticleTag = '<?xml version="1.0" encoding="UTF-8"?>' +
                                       '<article>' +
                                         '<front>' +
                                           '<article-meta>' +
                                             '<related-article/>' +
                                           '</article-meta>' +
                                         '</front>' +
                                       '</article>';

  let xmlBufferWithRelatedArticleTag = Buffer.from(xmlStringWithRelatedArticleTag, "binary");

  let xmlStringWithoutRelatedArticleTag = '<?xml version="1.0" encoding="UTF-8"?>' +
                                          '<article>' +
                                            '<front>' +
                                              '<article-meta/>' +
                                            '</front>' +
                                          '</article>';

  let xmlBufferWithoutRelatedArticleTag = Buffer.from(xmlStringWithoutRelatedArticleTag, "binary");                                        

  let result = stripRelatedArticleTags(xmlBufferWithRelatedArticleTag);
  expect(result.toString()).toBe(xmlStringWithoutRelatedArticleTag);

  result = stripRelatedArticleTags(xmlBufferWithoutRelatedArticleTag);
  expect(result.toString()).toBe(xmlStringWithoutRelatedArticleTag);
});
