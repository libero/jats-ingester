/*
Helper function designed to be used with the Apache Airflow Bash Operator.

Calls the default function in the script specified as the third argument and logs
the returned value to console, which in turn is stored in the Airflow XCom table.
 */
const AWS = require('aws-sdk');


async function functionCaller() {

  let fetchedData, returnedData, uploadedData;
  // get callable from script which is expected to be the third argument
  console.log('Getting callable from ', process.argv[2]);
  let callable = require(process.argv[2]);
  // AWS S3 key expected to be forth argument
  let key = process.argv[3];


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

  let s3 = new AWS.S3(s3ConfigParams);

  // if S3 Key was passed then retrieve the object
  if (key) {

    let s3Params = {
      Bucket: process.env.COMPLETED_TASKS_BUCKET,
      Key: key
    };

    console.log('Getting the following from S3: ', s3Params);
    fetchedData = await s3.getObject(s3Params, (error) => {
      if (error) {
        throw error;
      }
    }).promise();

    console.log('Data received from S3: ', fetchedData);
  }

  if (fetchedData) {
    console.log('Calling callable with response body');
    returnedData = callable(fetchedData.Body);
  } else {
    console.log('Calling callable without any arguments');
    returnedData = callable();
  }


  // upload the returned value to S3
  if (returnedData) {
    console.log('Data returned from callable: ', returnedData);

    // check if the returned object is a buffer
    let typeOfReturnedData = Object.prototype.toString.call(returnedData);
    let desiredType = Object.prototype.toString.call(Buffer.from(''));

    if (typeOfReturnedData !== desiredType) {
      throw "return value from " + process.argv[2] + " is not of type Buffer"
    }

    key = process.env.AIRFLOW_CTX_DAG_ID + "/" +
          process.env.AIRFLOW_CTX_TASK_ID + "/" +
          process.env.AIRFLOW_CTX_DAG_RUN_ID + "/" +
          process.env.FILE_NAME;

    let s3Params = {
      Bucket: process.env.COMPLETED_TASKS_BUCKET,
      Key: key,
      Body: returnedData
    };
    console.log('Uploading to S3: ', s3Params);
    uploadedData = await s3.upload(s3Params, (error) => {
      if (error) {
        throw error;
      }
    }).promise();

    // return Key back to Airflow for the next task
    console.log('The next line will be stored in Airflow\'s ' +
                'XCom table which can be pulled by upstream tasks');
    console.log(uploadedData.Key);
  }

}

module.exports = functionCaller;

// if this script has been called directly then run the code in the if block
// equivalent to python's __name__ == '__main__' comparison
if (!module.parent) {
  functionCaller();
}
