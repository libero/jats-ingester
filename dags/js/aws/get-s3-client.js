const AWS = require('aws-sdk');

function getS3Client() {

  let s3ConfigParams = {
    apiVersion: '2006-03-01',
    maxRetries: 3,
    s3ForcePathStyle: true,
    httpOptions: {
      connectTimeout: 5000
    }
  };
  // set s3 to use local container by setting the ENDPOINT_URL environment variable
  if (process.env.ENDPOINT_URL) {
    s3ConfigParams.endpoint = new AWS.Endpoint(process.env.ENDPOINT_URL);
  }

  console.log('AWS S3 params: ', s3ConfigParams);
  return new AWS.S3(s3ConfigParams);
}

module.exports = getS3Client;
