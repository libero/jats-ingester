const fs = require('fs');
const Zip = require('adm-zip');
const s3Utils = require('../aws/s3-utils');
const fu = require('../IO/file-utils');


async function extractArchivedFilesToBucket() {

  let s3Params = {
    Bucket: process.env.SOURCE_BUCKET,
    Key: process.env.ARCHIVE_FILE_NAME
  };
  let tempFileName = await s3Utils.getObjectToFile(s3Params);

  console.log(tempFileName, 'File size after awaiting getObjectToFile:', fs.statSync(tempFileName).size);

  let archive = new Zip(tempFileName);
  s3Params = {Bucket: process.env.DESTINATION_BUCKET};

  for (let entry of archive.getEntries()) {
    if (entry.isDirectory) {
      continue;
    }

    // TODO: stream data to s3 asynchronously
    s3Params.Key = process.env.ARCHIVE_FILE_NAME.replace(new RegExp('\\.\\w+$'), '') + '/' + entry.entryName;
    s3Params.Body = entry.getData();

    await s3Utils.upload(s3Params);
  }

  // remove temp file if all succeeded
  await fu.deleteFile(tempFileName);

}

module.exports = extractArchivedFilesToBucket;
