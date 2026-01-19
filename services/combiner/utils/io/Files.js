const fs = require('fs').promises;
const path = require('path');

async function readFilesAsStrings(folderPath) {
    try {
        const files = await fs.readdir(String(folderPath));

        // Filter numeric filenames and sort
        const numericFiles = files
            .filter(f => /^\d+$/.test(f))
            .sort((a, b) => Number(a) - Number(b));

        const stringsList = [];
        for (const file of numericFiles) {
            const filePath = path.join(folderPath, file);
            const data = await fs.readFile(filePath); // Buffer
            stringsList.push(data.toString()); // Convert bytes to string
        }

        return stringsList; // Array of strings
    } catch (err) {
        console.error('Error:', err);
        return [];
    }
}

module.exports = {
    readFilesAsStrings
};