const fs = require('fs');


module.exports.deleteFile = async (filePath) => {
  if (fs.existsSync(filePath)) {
    await fs.unlink(filePath, (error) => {
      if (error) throw error;
      console.log('successfully deleted ' + filePath);
    });
  } else {
    console.log(filePath, 'does not exist. Cancelling call to delete file.')
  }
};
