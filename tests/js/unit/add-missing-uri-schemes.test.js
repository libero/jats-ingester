const addMissingURIScheme = require(process.env.AIRFLOW_HOME + '/dags/js/tasks/add-missing-uri-schemes');

test('adds http:// to xlink:href attributes starting with www.', () => {
  let xmlStringWithoutSchemes = '<?xml version="1.0" encoding="UTF-8"?>' +
                                '<test xmlns:xlink="http://www.w3.org/1999/xlink">' +
                                  '<tag xlink:href="www.test-url.com" data="test"/>' +
                                  '<tag xlink:href="http://test-url.com"/>' +
                                  '<tag data="test" xlink:href="www.test-url.com">' +
                                    'test text' +
                                  '</tag>' +
                                '</test>';

  let xmlStringWithSchemes = '<?xml version="1.0" encoding="UTF-8"?>' +
                             '<test xmlns:xlink="http://www.w3.org/1999/xlink">' +
                               '<tag xlink:href="http://www.test-url.com" data="test"/>' +
                               '<tag xlink:href="http://test-url.com"/>' +
                               '<tag data="test" xlink:href="http://www.test-url.com">' +
                                 'test text' +
                               '</tag>' +
                             '</test>';

  let xmlBufferWithoutSchemes = Buffer.from(xmlStringWithoutSchemes);
  let xmlBufferWithSchemes = Buffer.from(xmlStringWithSchemes);

  let result = addMissingURIScheme(xmlBufferWithoutSchemes);
  expect(result.toString()).toBe(xmlStringWithSchemes);

  result = addMissingURIScheme(xmlBufferWithSchemes);
  expect(result.toString()).toBe(xmlStringWithSchemes);
});