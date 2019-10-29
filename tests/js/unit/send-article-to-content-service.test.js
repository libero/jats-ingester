const axios = require('axios');
const sendArticleToContentService = require(process.env.AIRFLOW_HOME + '/dags/js/tasks/send-article-to-content-service');

// original definitions to be mocked
let axiosPutOriginal = axios.put;

let liberoXml = '<?xml version="1.0" encoding="UTF-8"?>' +
                '<item xmlns:jats="http://jats.nlm.nih.gov" xmlns="http://libero.pub">' +
                  '<meta>' +
                    '<id>00666</id>' +
                    '<service>test-service</service>' +
                  '</meta>' +
                  '<jats:article/>' +
                '</item>';


let contentStoreErrorResponseXml = '<?xml version="1.0" encoding="UTF-8"?>' +
                                   '<problem xmlns="urn:ietf:rfc:7807" xml:lang="en">' +
                                     '<status>400</status>' +
                                     '<title>Failed to load asset</title>' +
                                     '<details>Failed to load https://unstable-jats-ingester-expanded.' +
                                              's3.amazonaws.com/elife-00666-vor-r1/10.7554/eLife.00666.004 ' +
                                              'due to "404 Not Found".' +
                                     '</details>' +
                                   '</problem>';

let liberoXmlBuffer = Buffer.from(liberoXml);


describe('Test sendArticleToContentService', () => {

  beforeEach(() => {
    process.env = {
      SERVICE_URL: 'http://test-service.org'
    };

    axios.put = axiosPutOriginal;
  });

  test('successful request to SERVICE_URL', async () => {
    axios.put = jest.fn(() => {
      return Promise.resolve({
        status: 200,
        statusText: 'OK'
      })
    });

    await sendArticleToContentService(liberoXmlBuffer);

    expect(axios.put).toHaveBeenCalledTimes(1);
    expect(axios.put).toHaveBeenCalledWith(
      'http://test-service.org/items/00666/versions/1',
      liberoXml,
      {headers: {'content-type': 'application/xml'}}
    );

  });

  test('400 response from SERVICE_URL', async () => {
    axios.put = jest.fn(() => {
      return Promise.resolve({
        status: 400,
        data: contentStoreErrorResponseXml
      })
    });

    expect.assertions(1);

    try {
      await sendArticleToContentService(liberoXmlBuffer);
    } catch (error){
      expect(error.message).toBe('PUT request to http://test-service.org/items/00666/versions/1 Failed: ' +
                                 '400 Failed to load https://unstable-jats-ingester-expanded.' +
                                 's3.amazonaws.com/elife-00666-vor-r1/10.7554/eLife.00666.004 ' +
                                 'due to "404 Not Found".');
    }
  });

  test('unsuccessful request to SERVICE_URL', async () => {
    axios.put = jest.fn(() => {
      return Promise.reject(new Error('test error'))
    });

    expect.assertions(1);

    try {
      await sendArticleToContentService(liberoXmlBuffer);
    } catch (error) {
      expect(error.message).toBe('test error')
    }
  })

});
