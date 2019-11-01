const Zip = require('adm-zip');
const libxmljs = require('libxmljs');
const s3Utils = require('../aws/s3-utils');
const fu = require('../IO/file-utils');
const jatsXml = require('../xml/jats-xml');


async function getJATSArticle() {

  let s3Params = {
    Bucket: process.env.SOURCE_BUCKET,
    Key: process.env.ARCHIVE_FILE_NAME
  };
  let tempFileName = await s3Utils.getObjectToFile(s3Params);

  let data;
  let archive = new Zip(tempFileName);

  for (let entry of archive.getEntries()) {

    if (entry.isDirectory) {
      continue;
    }

    if (entry.entryName.endsWith('.xml')) {
      let xmlDoc = libxmljs.parseXml(entry.getData().toString());

      if (jatsXml.isJATSArticle(xmlDoc)) {
        data = entry.getData();
        break;
      }
    }

  }
  await fu.deleteFile(tempFileName);

  if (data) {
    return data;
  }

  throw new Error('Unable to find JATS article in ' + process.env.ARCHIVE_FILE_NAME);

}

module.exports = getJATSArticle;
