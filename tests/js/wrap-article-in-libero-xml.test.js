const wrapArticleInLiberoXML = require(process.env.AIRFLOW_HOME + '/dags/js/tasks/wrap-article-in-libero-xml');

test('wrap article xml with libero xml using elife zip', () => {

  process.env = {
    ARCHIVE_FILE_NAME: 'elife-00666-vor-r1.zip',
    ARTICLE_ASSETS_URL: 'https://test-expanded-bucket.test.com',
    SERVICE_NAME: 'test-service'
  };


  let articleXML = '<?xml version="1.0" encoding="UTF-8"?>' +
                   '<article xmlns:ali="http://www.niso.org/schemas/ali/1.0/"' +
                           ' xmlns:mml="http://www.w3.org/1998/Math/MathML"' +
                           ' xmlns:xlink="http://www.w3.org/1999/xlink"' +
                           ' article-type="research-article"' +
                           ' dtd-version="1.2">' +
                     '<front>' +
                       '<article-meta>' +
                         '<article-id pub-id-type="publisher-id">00666</article-id>' +
                       '</article-meta>' +
                     '</front>' +
                   '</article>';

  let liberoXML = '<?xml version="1.0" encoding="UTF-8"?>' +
                  '<item xmlns:jats="http://jats.nlm.nih.gov" xmlns="http://libero.pub">' +
                    '<meta>' +
                      '<id>00666</id>' +
                      '<service>test-service</service>' +
                    '</meta>' +
                    '<jats:article xmlns:ali="http://www.niso.org/schemas/ali/1.0/"' +
                                 ' xmlns:mml="http://www.w3.org/1998/Math/MathML"' +
                                 ' xmlns:xlink="http://www.w3.org/1999/xlink"' +
                                 ' article-type="research-article"' +
                                 ' dtd-version="1.2"' +
                                 ' xml:base="https://test-expanded-bucket.test.com/elife-00666-vor-r1/">' +
                      '<jats:front>' +
                        '<jats:article-meta>' +
                          '<jats:article-id pub-id-type="publisher-id">00666</jats:article-id>' +
                        '</jats:article-meta>' +
                      '</jats:front>' +
                    '</jats:article>' +
                  '</item>';


  let result = wrapArticleInLiberoXML(Buffer.from(articleXML, 'binary'));
  expect(result.toString()).toBe(liberoXML);
});

test('wrap article xml with libero xml using biorxiv meca', () => {

  process.env = {
    ARCHIVE_FILE_NAME: 'biorxiv-00666.meca',
    ARTICLE_ASSETS_URL: 'https://test-expanded-bucket.test.com',
    SERVICE_NAME: 'test-service'
  };

  let articleXML = '<?xml version="1.0" encoding="UTF-8"?>' +
                   '<article xmlns:ali="http://www.niso.org/schemas/ali/1.0/"' +
                           ' xmlns:mml="http://www.w3.org/1998/Math/MathML"' +
                           ' xmlns:xlink="http://www.w3.org/1999/xlink"' +
                           ' article-type="research-article"' +
                           ' dtd-version="1.2">' +
                     '<front>' +
                       '<article-meta>' +
                         '<article-id pub-id-type="publisher-id">00666</article-id>' +
                       '</article-meta>' +
                     '</front>' +
                   '</article>';

  let liberoXML = '<?xml version="1.0" encoding="UTF-8"?>' +
                  '<item xmlns:jats="http://jats.nlm.nih.gov" xmlns="http://libero.pub">' +
                    '<meta>' +
                      '<id>00666</id>' +
                      '<service>test-service</service>' +
                    '</meta>' +
                    '<jats:article xmlns:ali="http://www.niso.org/schemas/ali/1.0/"' +
                                 ' xmlns:mml="http://www.w3.org/1998/Math/MathML"' +
                                 ' xmlns:xlink="http://www.w3.org/1999/xlink"' +
                                 ' article-type="research-article"' +
                                 ' dtd-version="1.2"' +
                                 ' xml:base="https://test-expanded-bucket.test.com/biorxiv-00666/content/">' +
                      '<jats:front>' +
                        '<jats:article-meta>' +
                          '<jats:article-id pub-id-type="publisher-id">00666</jats:article-id>' +
                        '</jats:article-meta>' +
                      '</jats:front>' +
                    '</jats:article>' +
                  '</item>';


  let result = wrapArticleInLiberoXML(Buffer.from(articleXML, 'binary'));
  expect(result.toString()).toBe(liberoXML);
});
