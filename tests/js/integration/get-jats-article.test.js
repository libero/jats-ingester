const fs = require('fs');
const libxmljs = require('libxmljs');
const getJATSArticle = require(process.env.AIRFLOW_HOME + '/dags/js/tasks/get-jats-article');
const jatsXml = require(process.env.AIRFLOW_HOME + '/dags/js/xml/jats-xml');

let unlinkSyncOriginal = fs.unlinkSync;


describe('test getJATSArticle', () => {

  beforeEach(() => {
    process.env = {
      AIRFLOW_CTX_DAG_ID: 'dag_1',
      AIRFLOW_CTX_TASK_ID: 'task_1',
      AIRFLOW_CTX_DAG_RUN_ID: 'dag_run_1',
      AIRFLOW_CTX_EXECUTION_DATE: new Date(2019, 1, 1).toISOString(),
      ARCHIVE_FILE_NAME: 'elife-00666-vor-r1.zip',
      COMPLETED_TASKS_BUCKET: 'dev-jats-ingester-completed-tasks',
      DESTINATION_BUCKET: 'dev-jats-ingester-expanded',
      ENDPOINT_URL: 'http://s3:9000',
      SOURCE_BUCKET: 'dev-jats-ingester-incoming'
    };

    fs.unlinkSync = unlinkSyncOriginal;
  });

  test('returns a jats article buffer', async () => {
    fs.unlinkSync = jest.fn();

    let jatsArticleBuffer = await getJATSArticle();
    let jatsArticle = libxmljs.parseXml(jatsArticleBuffer.toString());

    expect(jatsXml.isJATSArticle(jatsArticle)).toBeTruthy();
    expect(fs.unlinkSync).toHaveBeenCalledTimes(1);
  });

  // TODO: create test with zip without jats article

});
