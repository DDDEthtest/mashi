const http = require('http');
const {PORT} = require('../../../configs/GifConfig');
const {generateGif, generateApng} = require('../services/GifService');


async function startServer() {
    http.createServer(async (req, res) => {
        if (req.method === 'POST') {
            let body = '';
            req.on('data', chunk => body += chunk.toString());
            req.on('end', async () => {
                try {
                    if (!body) throw new Error("Empty body received");
                    const data = JSON.parse(body);

                    const {
                        temp_dir: tempDir,
                        max_t: maxT,
                        is_apng: isApng
                    } = data;

                    let resultPath;

                    if (isApng) {
                        // Call the updated, simplified APNG function
                        resultPath = await generateApng(tempDir, maxT);
                    } else {
                        // Call original GIF function with all flags
                        resultPath = await generateGif(
                            tempDir,
                            maxT,
                            data.is_higher_res,
                            data.is_longer,
                            data.is_smoother,
                            data.is_faster,
                            data.is_slower
                        );
                    }

                    res.writeHead(200, {'Content-Type': 'text/plain'});
                    res.end(resultPath);
                } catch (err) {
                    console.error("Internal Error:", err);
                    res.writeHead(500);
                    res.end(err.message);
                }
            });
        }
    }).listen(PORT, () => console.log(`Server listening on ${PORT}`));
}

module.exports = {
    startServer
};