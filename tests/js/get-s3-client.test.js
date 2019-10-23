const AWS = require('aws-sdk');

const getS3Client = require(process.env.AIRFLOW_HOME + '/dags/js/aws/get-s3-client.js');


// original definitions to be mocked
let AWSS3Original = AWS.S3;


describe('Test getS3Client', () => {

  beforeEach(() => {
    process.env = {};
  });

  afterEach(() => {
    AWS.S3 = AWSS3Original;
  });

  test('will specify an AWS Endpoint if ENDPOINT_URL environment variable is set', () => {

    process.env.ENDPOINT_URL = 'http://s3:9000';

    AWS.S3 = jest.fn();

    getS3Client();

    expect(AWS.S3.mock.calls.length).toBe(1);
    expect(AWS.S3.mock.calls[0][0].endpoint.href).toBe('http://s3:9000/');
  });


  test('will not specify an AWS Endpoint if ENDPOINT_URL environment variable is not set', () => {
    AWS.S3 = jest.fn();

    getS3Client();

    expect(AWS.S3.mock.calls.length).toBe(1);
    expect(AWS.S3.mock.calls[0][0].endpoint).toBe(undefined);
  });


});
