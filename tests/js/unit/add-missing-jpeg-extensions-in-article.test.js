const addMissingJPEGExtensionsInArticle = require(process.env.AIRFLOW_HOME + '/dags/js/tasks/add-missing-jpeg-extensions-in-article');

test('adds ".jpeg" to the value of xlink:href attributes that include mime-type="image" and mime-subtype="jpeg"', () => {
  let xmlStringWithoutJPEGExtensions = '<?xml version="1.0" encoding="UTF-8"?>' +
                                       '<test xmlns:xlink="http://www.w3.org/1999/xlink">' +
                                         '<graphic xlink:href="fig1" mimetype="image" mime-subtype="jpeg"/>' +
                                       '</test>';

  let xmlStringWithJPEGExtensions = '<?xml version="1.0" encoding="UTF-8"?>' +
                                    '<test xmlns:xlink="http://www.w3.org/1999/xlink">' +
                                      '<graphic xlink:href="fig1.jpg" mimetype="image" mime-subtype="jpeg"/>' +
                                    '</test>';

  let xmlBufferWithoutJPEGExtensions = Buffer.from(xmlStringWithoutJPEGExtensions);
  let xmlBufferWithJPEGExtensions = Buffer.from(xmlStringWithJPEGExtensions);

  let result = addMissingJPEGExtensionsInArticle(xmlBufferWithoutJPEGExtensions);
  expect(result.toString()).toBe(xmlStringWithJPEGExtensions);

  result = addMissingJPEGExtensionsInArticle(xmlBufferWithJPEGExtensions);
  expect(result.toString()).toBe(xmlStringWithJPEGExtensions);
});