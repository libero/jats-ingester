const libxmljs = require('libxmljs');
const jatsXml = require(process.env.AIRFLOW_HOME + '/dags/js/xml/jats-xml');


test('jats-xml.getArticleID', () => {
  let jatsXMLSamples = [
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<article>' +
      '<front>' +
        '<article-meta>' +
          '<article-id pub-id-type="publisher-id">00666</article-id>' +
        '</article-meta>' +
      '</front>' +
    '</article>',
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<article>' +
      '<front>' +
        '<article-meta>' +
          '<article-id pub-id-type="manuscript">00666</article-id>' +
        '</article-meta>' +
      '</front>' +
    '</article>',
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<article>' +
      '<front>' +
        '<article-meta>' +
          '<elocation-id>00666</elocation-id>' +
        '</article-meta>' +
      '</front>' +
    '</article>',
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<article>' +
      '<front>' +
        '<article-meta>' +
          '<article-id pub-id-type="doi">00666</article-id>' +
        '</article-meta>' +
      '</front>' +
    '</article>',
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<article>' +
      '<front>' +
        '<article-meta>' +
          '<article-id pub-id-type="publisher-id">00666</article-id>' +
          '<article-id pub-id-type="manuscript">00666</article-id>' +
          '<elocation-id>00666</elocation-id>' +
          '<article-id pub-id-type="doi">00666</article-id>' +
        '</article-meta>' +
      '</front>' +
    '</article>'
  ];

  expect.assertions(jatsXMLSamples.length);

  jatsXMLSamples.forEach((xml) => {
    let xmlDoc = libxmljs.parseXml(xml);
    expect(jatsXml.getArticleID(xmlDoc)).toBe('00666');
  })
});

test('jats-xml.getArticleID throws error when unable to find id using xpaths', () => {
  let xmlDoc = libxmljs.parseXml('<article><front><article-meta></article-meta></front></article>');
  expect.assertions(1);
  try {
    jatsXml.getArticleID(xmlDoc);
  } catch (error) {
    expect(error.message).toBe('Unable to find article ID');
  }
});