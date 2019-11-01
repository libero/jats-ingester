const axios = require('axios');


async function sendPostRequestToReindexSearchService() {
  console.log('Sending POST request to:', process.env.SEARCH_URL);

  let response = await axios.post(process.env.SEARCH_URL);

  if (response.status >= 400) {
    throw new Error('POST request to ' + process.env.SEARCH_URL + ' Failed: ' +
                    response.status + ' ' + response.statusText);
  }

  console.log('RESPONSE:', response.status, response.statusText)
}

module.exports = sendPostRequestToReindexSearchService;
