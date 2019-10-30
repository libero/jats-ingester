const fs = require('fs');

const Zip = require('adm-zip');
const libxmljs = require('libxmljs');
const uuidv4 = require('uuid/v4');

const getS3Client = require('../aws/get-s3-client');
const jatsXml = require('../xml/jats-xml');


async function getJATSArticle() {

  function deleteFile(fileName) {
    fs.unlinkSync(fileName);
    console.log('successfully deleted ' + fileName);
  }

  let tempFileName = '/tmp/' + uuidv4();
  console.log('Temp file name =', tempFileName);

  let fileStream = fs.createWriteStream(tempFileName);
  let s3 = getS3Client();

  let s3Params = {
    Bucket: process.env.SOURCE_BUCKET,
    Key: process.env.ARCHIVE_FILE_NAME
  };

  console.log('Getting the following from S3: ', s3Params);
  await new Promise((resolve, reject) => {
    s3.getObject(s3Params).createReadStream()
      .on('end', () => {
        return resolve();
    }).on('error', (error) => {
        deleteFile(tempFileName);
        return reject(error);
    }).pipe(fileStream)});

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
  deleteFile(tempFileName);

  if (data) {
    return data;
  }

  throw new Error('Unable to find JATS article in ' + process.env.ARCHIVE_FILE_NAME);

}

module.exports = getJATSArticle;
