const AWS = require('aws-sdk');

const getS3Client = require(process.env.AIRFLOW_HOME + '/dags/js/aws/get-s3-client.js');


describe('Test getS3Client', () => {

  test('will specify an AWS Endpoint if ENDPOINT_URL environment variable is set', () => {

    process.env.ENDPOINT_URL = 'http://s3:9000';

    // AWS mocks
    let AWSS3 = AWS.S3;
    AWS.S3 = jest.fn();

    expect.assertions(2);
    let s3 = getS3Client();
    expect(AWS.S3.mock.calls.length).toBe(1);
    expect(AWS.S3.mock.calls[0][0].endpoint.href).toBe('http://s3:9000/');

    // teardown
    AWS.S3 = AWSS3;
  });


  test('will not specify an AWS Endpoint if ENDPOINT_URL environment variable is not set', () => {

    delete process.env.ENDPOINT_URL;

    // AWS mocks
    let AWSS3 = AWS.S3;
    AWS.S3 = jest.fn();

    expect.assertions(2);
    let s3 = getS3Client();
    expect(AWS.S3.mock.calls.length).toBe(1);
    expect(AWS.S3.mock.calls[0][0].endpoint).toBe(undefined);

    // teardown
    AWS.S3 = AWSS3;
  });


});
