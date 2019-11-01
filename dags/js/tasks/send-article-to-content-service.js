const axios = require('axios');
const libxmljs = require('libxmljs');
const liberoXml = require('../xml/libero-xml');


async function sendArticleToContentService(xmlStringBuffer) {
  let xmlDoc = libxmljs.parseXml(xmlStringBuffer.toString());
  let articleID = liberoXml.getContentID(xmlDoc);
  let url = process.env.SERVICE_URL + '/items/' + articleID + '/versions/1';

  console.log('Sending PUT request to:', url);

  let response = await axios.put(url, xmlStringBuffer.toString(), {headers: {'content-type': 'application/xml'}});

  if (response.status >= 400) {

    let errorXml = libxmljs.parseXml(response.data);
    let details = errorXml.find('//problem:details', {"problem": "urn:ietf:rfc:7807"})[0].text();

    throw new Error('PUT request to ' + url + ' Failed: ' + response.status + ' ' + details);
  }

  console.log('RESPONSE: ', response.status, response.statusText);

}

module.exports = sendArticleToContentService;
