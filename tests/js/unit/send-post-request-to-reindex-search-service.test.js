const axios = require('axios');
const sendPostRequestToReindexSearchService = require(process.env.AIRFLOW_HOME + '/dags/js/tasks/send-post-request-to-reindex-search-service');

// original definitions to be mocked
let axiosPostOriginal = axios.post;


describe('Test sendPostRequestToReindexSearchService', () => {

  beforeEach(() => {
    process.env = {
      SEARCH_URL: 'http://test-search-service.org'
    };

    axios.post = axiosPostOriginal;
  });

  test('successful request to SEARCH_URL', async () => {
    axios.post = jest.fn(() => {
      return Promise.resolve({
        status: 200,
        statusText: 'OK'
      })
    });

    await sendPostRequestToReindexSearchService();

    expect(axios.post).toHaveBeenCalledTimes(1);
    expect(axios.post).toHaveBeenCalledWith('http://test-search-service.org');

  });

  test('400 response from SEARCH_URL', async () => {
    axios.post = jest.fn(() => {
      return Promise.resolve({
        status: 404,
        statusText: 'Not Found'
      })
    });

    expect.assertions(1);

    try {
      await sendPostRequestToReindexSearchService();
    } catch (error){
      expect(error.message).toBe('POST request to http://test-search-service.org Failed: 404 Not Found');
    }
  });

  test('unsuccessful request to SEARCH_URL', async () => {
    axios.post = jest.fn(() => {
      return Promise.reject(new Error('test error'))
    });

    expect.assertions(1);

    try {
      await sendPostRequestToReindexSearchService();
    } catch (error) {
      expect(error.message).toBe('test error')
    }
  })

});
