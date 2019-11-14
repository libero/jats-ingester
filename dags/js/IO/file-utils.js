const fs = require('fs');
const util = require('util');


module.exports.deleteFile = async (filePath) => {
  if (await util.promisify(fs.exists)(filePath)) {
    await util.promisify(fs.unlink)(filePath);
    console.log('successfully deleted ' + filePath);
  } else {
    console.log(filePath, 'does not exist. Cancelling call to delete file.')
  }
};
