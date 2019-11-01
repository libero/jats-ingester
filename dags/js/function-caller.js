/*
Helper function designed to be used with the Apache Airflow Bash Operator.

Calls the default function in the script specified as the third argument and logs
the returned value to console, which in turn is stored in the Airflow XCom table.
 */
const s3Utils = require(process.env.AIRFLOW_HOME + '/dags/js/aws/s3-utils.js');

async function functionCaller() {

  let fetchedData, returnedData, uploadedData;

  // get callable from script which is expected to be the third argument
  console.log('Getting callable from ', process.argv[2]);
  let callable = require(process.argv[2]);

  // AWS S3 key expected to be forth argument
  let key = process.argv[3];

  // if S3 Key was passed then retrieve the object
  if (key) {

    let s3Params = {
      Bucket: process.env.COMPLETED_TASKS_BUCKET,
      Key: key
    };

    fetchedData = await s3Utils.getObject(s3Params);
  }

  if (fetchedData) {
    console.log('Calling callable with response body');
    returnedData = await callable(fetchedData.Body);
  } else {
    console.log('Calling callable without any arguments');
    returnedData = await callable();
  }


  // upload the returned value to S3
  if (returnedData) {
    console.log('Data returned from callable: ', returnedData);

    // check if the returned object is a buffer
    let typeOfReturnedData = Object.prototype.toString.call(returnedData);
    let desiredType = Object.prototype.toString.call(Buffer.from(''));

    if (typeOfReturnedData !== desiredType) {
      throw new Error("return value from " + process.argv[2] + " is not of type Buffer");
    }

    key = process.env.AIRFLOW_CTX_DAG_ID + "/" +
          process.env.AIRFLOW_CTX_TASK_ID + "/" +
          process.env.AIRFLOW_CTX_EXECUTION_DATE + "_" +
          process.env.AIRFLOW_CTX_DAG_RUN_ID;

    let s3Params = {
      Bucket: process.env.COMPLETED_TASKS_BUCKET,
      Key: key,
      Body: returnedData
    };

    uploadedData = await s3Utils.upload(s3Params);

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
  functionCaller().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
