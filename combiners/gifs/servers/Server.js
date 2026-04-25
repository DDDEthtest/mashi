const http = require('http');
const {PORT} = require('../configs/ServerConfig');
const {generateGif} = require('../services/Gif');


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
                        max_t: maxT
                    } = data;

                    let resultPath = await generateGif(
                        tempDir,
                        maxT
                    );

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