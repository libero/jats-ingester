const updateTiffReferencesToJPEGInArticle = require(process.env.AIRFLOW_HOME + '/dags/js/tasks/update-tiff-references-to-jpeg-in-article');

test('update attribute information for tags with tiff information to jpeg information', () => {
  let xmlStringWithTIFFs = '<?xml version="1.0" encoding="UTF-8"?>' +
                           '<test xmlns:xlink="http://www.w3.org/1999/xlink">' +
                             '<graphic xlink:href="fig1.tif" mimetype="image" mime-subtype="tiff"/>' +
                             '<graphic mimetype="image" mime-subtype="tiff" xlink:href="fig1.tif"/>' +
                             '<graphic xlink:href="fig1.tif"/>' +
                           '</test>';

  let xmlStringWithJPEGs = '<?xml version="1.0" encoding="UTF-8"?>' +
                           '<test xmlns:xlink="http://www.w3.org/1999/xlink">' +
                             '<graphic xlink:href="fig1.jpg" mimetype="image" mime-subtype="jpeg"/>' +
                             '<graphic mimetype="image" mime-subtype="jpeg" xlink:href="fig1.jpg"/>' +
                             '<graphic xlink:href="fig1.jpg"/>' +
                           '</test>';

  let xmlBufferWithTIFFs = Buffer.from(xmlStringWithTIFFs);
  let xmlBufferWithJPEGs = Buffer.from(xmlStringWithJPEGs);

  let result = updateTiffReferencesToJPEGInArticle(xmlBufferWithTIFFs);
  expect(result.toString()).toBe(xmlStringWithJPEGs);

  result = updateTiffReferencesToJPEGInArticle(xmlBufferWithJPEGs);
  expect(result.toString()).toBe(xmlStringWithJPEGs);
});