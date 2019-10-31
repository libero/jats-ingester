const fs = require('fs');
const sharp = require('sharp');
const uuidv4 = require('uuid/v4');
const getS3Client = require('../aws/get-s3-client');
const io = require('../IO/io');

async function convertTiffImagesInExpandedBucketToJpegImages() {

  let s3 = getS3Client();

  let s3Params = {
    Bucket: process.env.DESTINATION_BUCKET,
    Prefix: process.env.ARCHIVE_FILE_NAME.replace(new RegExp('\\.\\w+$'), '')
  };
  let response = await s3.listObjectsV2(s3Params, (error) => {
    if (error) {
      throw error;
    }
  }).promise();

  for (let item of response.Contents) {

    if (item.Key.endsWith('.tif')) {

      let tempDownloadFileName = '/tmp/' + uuidv4();
      console.log('Temp download file name =', tempDownloadFileName);

      let s3Params = {
        Bucket: process.env.DESTINATION_BUCKET,
        Key: item.Key
      };

      console.log('Getting the following from S3: ', s3Params);
      await new Promise((resolve, reject) => {
        s3.getObject(s3Params).createReadStream()
          .on('end', () => {
            return resolve();
        }).on('error', async (error) => {
            await io.deleteFile(tempDownloadFileName);
            return reject(error);
        }).pipe(fs.createWriteStream(tempDownloadFileName))
      });

      // TODO: use streams instead of Buffer
      console.log('Converting ' + item.Key + ' to JPEG');
      let convertedImage = await sharp(tempDownloadFileName).jpeg().toBuffer();

      // we no long need the temp file for storing downloaded data
      await io.deleteFile(tempDownloadFileName);

      s3Params.Key = item.Key.replace('.tif', '.jpg');
      s3Params.Body = convertedImage;

      console.log('Uploading:', s3Params.Bucket, s3Params.Key);
      let response = await s3.upload(s3Params, (error) => {
        if (error) {
          throw error;
        }
      }).promise();
      console.log(response.Location);

    }

  }
}

module.exports = convertTiffImagesInExpandedBucketToJpegImages;
