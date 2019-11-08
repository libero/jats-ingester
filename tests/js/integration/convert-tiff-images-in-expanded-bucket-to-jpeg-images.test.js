const s3Utils = require(process.env.AIRFLOW_HOME + '/dags/js/aws/s3-utils');
const convertTiffImagesInExpandedBucketToJpegImages = require(process.env.AIRFLOW_HOME + '/dags/js/tasks/convert-tiff-images-in-expanded-bucket-to-jpeg-images');
const extractArchivedFilesToBucket = require(process.env.AIRFLOW_HOME + '/dags/js/tasks/extract-archived-files-to-bucket');
const fu = require(process.env.AIRFLOW_HOME + '/dags/js/IO/file-utils');


describe('Test convertTiffImagesInExpandedBucketToJpegImages', () => {

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

    try {
      fu.deleteFile.mockRestore();
    } catch (error) {

    }
  });


  test('using elife-00666-vor-r1.zip', async () => {

    let destinationBucket = 'dev-jats-ingester-convert-tiff-00666';

    process.env.DESTINATION_BUCKET = destinationBucket;
    process.env.ARCHIVE_FILE_NAME = 'elife-00666-vor-r1.zip';

    await s3Utils.createBucket({Bucket: destinationBucket});

    await extractArchivedFilesToBucket();
    fu.deleteFile = jest.fn();

    await convertTiffImagesInExpandedBucketToJpegImages();

    let s3Params = {Bucket: destinationBucket, Prefix: 'elife-00666-vor-r1'};
    let response = await s3Utils.listObjectsV2(s3Params);

    let count = 0;
    for (let item of response.Contents) {
      if (item.Key.endsWith('.jpg')) {
        count++;
      }
    }
    expect(count).toBeGreaterThan(0);
    expect(fu.deleteFile).toHaveBeenCalledTimes(0);
  });


  test('using biorxiv-685172.meca', async () => {

    let destinationBucket = 'dev-jats-ingester-convert-tiff-685172';

    process.env.DESTINATION_BUCKET = destinationBucket;
    process.env.ARCHIVE_FILE_NAME = 'biorxiv-685172.meca';

    await s3Utils.createBucket({Bucket: destinationBucket});

    await extractArchivedFilesToBucket();
    fu.deleteFile = jest.fn();

    await convertTiffImagesInExpandedBucketToJpegImages();

    let s3Params = {Bucket: destinationBucket, Prefix: 'biorxiv-685172'};
    let response = await s3Utils.listObjectsV2(s3Params);

    let count = 0;
    for (let item of response.Contents) {
      if (item.Key.endsWith('.jpg')) {
        expect(item.Size).toBeGreaterThan(0);
        count++;
      }
    }
    // 5 image files downloaded
    expect(count).toBe(5);
    expect(fu.deleteFile).toHaveBeenCalledTimes(5);
  });

});
