const sharp = require('sharp');
const s3Utils = require('../aws/s3-utils');
const fu = require('../IO/file-utils');

async function convertTiffImagesInExpandedBucketToJpegImages() {

  let s3Params = {
    Bucket: process.env.DESTINATION_BUCKET,
    Prefix: process.env.ARCHIVE_FILE_NAME.replace(new RegExp('\\.\\w+$'), '')
  };
  let response = await s3Utils.listObjectsV2(s3Params);

  for (let item of response.Contents) {

    if (item.Key.endsWith('.tif')) {

      let s3Params = {
        Bucket: process.env.DESTINATION_BUCKET,
        Key: item.Key
      };

      let tempDownloadFileName = await s3Utils.getObjectToFile(s3Params);

      // TODO: use streams instead of Buffer
      console.log('Converting ' + item.Key + ' to JPEG');
      let convertedImage = await sharp(tempDownloadFileName).jpeg().toBuffer();

      // we no long need the temp file for storing downloaded data
      await fu.deleteFile(tempDownloadFileName);

      s3Params.Key = item.Key.replace('.tif', '.jpg');
      s3Params.Body = convertedImage;

      await s3Utils.upload(s3Params);
    }

  }
}

module.exports = convertTiffImagesInExpandedBucketToJpegImages;
