const libxmljs = require('libxmljs');
const jatsXml = require('../xml/jats-xml');
const namespaces = require('../xml/namespaces');


function wrapArticleInLiberoXML(xmlStringBuffer) {

  let xmlDoc = libxmljs.parseXml(xmlStringBuffer.toString());

  let articleID = jatsXml.getArticleID(xmlDoc);

  let base = process.env.ARTICLE_ASSETS_URL + '/' +
             process.env.ARCHIVE_FILE_NAME.replace(new RegExp('\\.\\w+$'), '') + '/';

  if (process.env.ARCHIVE_FILE_NAME.endsWith('.meca')) {
    base = base + 'content/';
  }

  xmlDoc.root().attr('xml:base', base);

  function addJATSPrefix(element) {
    element.name('jats:' + element.name());
    element.childNodes().forEach((child) => {
      addJATSPrefix(child);
    })
  }

  addJATSPrefix(xmlDoc.root());

  let newDoc = libxmljs.Document();

  let item = newDoc.node('item');
  item.defineNamespace('jats', namespaces.JATS);
  item.defineNamespace(namespaces.LIBERO);

  let meta = item.node('meta');
  meta.node('id', articleID);
  meta.node('service', process.env.SERVICE_NAME);

  item.addChild(xmlDoc.root());

  // adding false to document.toString should remove formatting but
  // a few newlines (\n) can still be found
  let xmlDocAsString = newDoc.toString(false);

  // actually remove formatting
  return xmlDocAsString.replace(new RegExp('\n', 'g'), '')
}

module.exports = wrapArticleInLiberoXML;
