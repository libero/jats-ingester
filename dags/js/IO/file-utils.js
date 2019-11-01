const fs = require('fs');


module.exports.deleteFile = async (filePath) => {
    await fs.unlink(filePath, (error) => {
      if (error) throw error;
      console.log('successfully deleted ' + filePath);
    });
  };
