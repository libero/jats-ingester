const FUNCTION_CALLER_SCRIPT_PATH = process.env.AIRFLOW_HOME + '/dags/js/function-caller.js';
const CALLABLE_SCRIPT_PATH = process.env.AIRFLOW_HOME + '/tests/js/test-callable.js';

const AWSMock = require('aws-sdk-mock');
const functionCaller = require(FUNCTION_CALLER_SCRIPT_PATH);

// original definitions to be mocked
let consoleLogOriginal = console.log;

// mock test callable
jest.mock(CALLABLE_SCRIPT_PATH);
// get mock object for assertions
const callable = require(CALLABLE_SCRIPT_PATH);


describe('Test functionCaller', () => {

  beforeEach(() => {
    process.argv = [
      '/usr/bin/node',
      FUNCTION_CALLER_SCRIPT_PATH,
      CALLABLE_SCRIPT_PATH
    ];

    process.env = {
      AIRFLOW_CTX_DAG_ID: 'dag_1',
      AIRFLOW_CTX_TASK_ID: 'task_1',
      AIRFLOW_CTX_DAG_RUN_ID: 'dag_run_1',
      AIRFLOW_CTX_EXECUTION_DATE: new Date(2019, 1, 1).toISOString(),
      COMPLETED_TASKS_BUCKET: 'completed-tasks-bucket'
    };

    callable.mockClear();
    console.log = consoleLogOriginal;
  });

  afterEach(() => {
    AWSMock.restore("S3");
  });

  test('can import and call callable from script', async () => {
    await functionCaller();
    expect(callable.mock.calls.length).toBe(1);
  });


  test('will get an object from AWS S3 using passed Key', async () => {
    process.argv = process.argv.concat(['MyKey']);
    process.env.ENDPOINT_URL = 'http://s3:9000';

    // AWS mocks
    AWSMock.mock("S3", "getObject", {Body: Buffer.from('test', 'binary')});

    await functionCaller();
    expect(callable.mock.calls.length).toBe(1);
    expect(callable.mock.calls[0][0].toString()).toBe('test');
  });


  test('will call callable without any arguments if AWS S3 Key is not passed', async () => {
    await functionCaller();
    expect(callable.mock.calls.length).toBe(1);
    expect(callable.mock.calls[0][0]).toBe(undefined);
  });


  test('will upload returned object from callable to AWS S3', async () => {
    // TODO: check arguments passed to S3.upload call if the Key matches expected Key

    let testKey = 'test/key';

    AWSMock.mock("S3", "upload", {Key: testKey});
    callable.mockReturnValue(Buffer.from('test'));
    console.log = jest.fn();

    await functionCaller();

    let lastLogCallIndex = console.log.mock.calls.length - 1;
    expect(console.log.mock.calls[lastLogCallIndex][0]).toBe(testKey);
  });


  test('throws error if returned object from callable is not of type Buffer', async () => {
    callable.mockReturnValue(42);

    expect.assertions(1);

    try {
      await functionCaller();
    } catch (error){
      expect(error).toBe("return value from /airflow/tests/js/test-callable.js is not of type Buffer");
    }
  });


  test('will not return AWS S3 Key if return value from callable not supplied', async () => {
    // TODO: check S3 response object

    let testKey = 'test/key';

    AWSMock.mock("S3", "upload", {Key: testKey});
    callable.mockReturnValue(undefined);
    console.log = jest.fn();

    await functionCaller();

    expect(callable.mock.calls.length).toBe(1);

    let lastLogCallIndex = console.log.mock.calls.length - 1;
    expect(console.log.mock.calls[lastLogCallIndex][0]).not.toBe(testKey);
  });

});
