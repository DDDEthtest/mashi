const http = require('http');
const {PORT} = require('../configs/Config');
const {generateGif} = require('../gif/GifMaker');


async function startServer() {
    http.createServer(async (req, res) => {
        if (req.method === 'POST') {
            let body = '';
            req.on('data', chunk => body += chunk.toString()); // ensure string
            req.on('end', async () => {
                try {
                    if (!body) throw new Error("Empty body received");
                    const data = JSON.parse(body);
                    const tempDir = data.temp_dir;
                    const maxT = data.max_t;
                    console.log("Received:", tempDir, maxT);

                    const gifPath = await generateGif(tempDir, maxT);
                    res.writeHead(200, {'Content-Type': 'text/plain'});
                    res.end(gifPath);
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