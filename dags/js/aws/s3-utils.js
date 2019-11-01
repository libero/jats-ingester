const fs = require('fs');
const AWS = require('aws-sdk');
const io = require('../IO/file-utils');
const uuidv4 = require('uuid/v4');


function createBucket(s3Params) {
  let s3 = this.getS3Client();
  s3.createBucket(s3Params, (error) => {
    if (error) throw error;
  });
}

async function getObject(s3Params) {
  let s3 = this.getS3Client();
  console.log('Getting the following from S3: ', s3Params);
  let response = await s3.getObject(s3Params, (error) => {
    if (error) {
      throw error;
    }
  }).promise();
  console.log('Data received from S3: ', response);
  return response;
}

async function getObjectToFile(s3Params) {
  let s3 = this.getS3Client();

  let tempDownloadFileName = '/tmp/' + uuidv4();
  console.log('Temp download file name =', tempDownloadFileName);

  console.log('Getting the following from S3: ', s3Params);

  await new Promise((resolve, reject) => {

    s3.getObject(s3Params).createReadStream()
      .on('end', () => {
        console.log(tempDownloadFileName, 'File size on end:', fs.statSync(tempDownloadFileName).size);
        resolve();
    }).on('error', async (error) => {
        console.log(tempDownloadFileName, 'File size on error:', fs.statSync(tempDownloadFileName).size);
        await io.deleteFile(tempDownloadFileName);
        reject(error);
    }).pipe(fs.createWriteStream(tempDownloadFileName))

  });

  return tempDownloadFileName;
}

function getS3Client() {
  let s3ConfigParams = {
    apiVersion: '2006-03-01',
    maxRetries: 3,
    httpOptions: {
      connectTimeout: 5000
    }
  };

  // set s3 to use local container by setting the ENDPOINT_URL environment variable
  if (process.env.ENDPOINT_URL) {
    s3ConfigParams.endpoint = new AWS.Endpoint(process.env.ENDPOINT_URL);
    s3ConfigParams.s3ForcePathStyle = true;
    console.log('Using AWS S3 endpoint: ', process.env.ENDPOINT_URL);
  }
  return new AWS.S3(s3ConfigParams);
}

async function listObjectsV2(s3Params) {
  let s3 = this.getS3Client();

  return await s3.listObjectsV2(s3Params, (error) => {
    if (error) throw error;
  }).promise();
}

async function upload(s3Params) {
  let s3 = this.getS3Client();

  console.log('Uploading:', s3Params.Bucket, s3Params.Key);
  let response = await s3.upload(s3Params, (error) => {
    if (error) throw error;
  }).promise();
  console.log(response.Location);
  return response;
}

module.exports.createBucket = createBucket;
module.exports.getObject = getObject;
module.exports.getObjectToFile = getObjectToFile;
module.exports.getS3Client = getS3Client;
module.exports.listObjectsV2 = listObjectsV2;
module.exports.upload = upload;
