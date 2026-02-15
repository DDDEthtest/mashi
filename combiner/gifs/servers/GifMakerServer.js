const http = require('http');
const {PORT} = require('../../../configs/GifConfig');
const {generateGif} = require('../services/GifService');


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

                    const isHigherRes = data.is_higher_res;
                    const isLonger = data.is_longer;
                    const isSmoother = data.is_smoother;
                    const isFaster = data.is_faster;
                    const isSlower = data.is_slower;

                    const gifPath = await generateGif(
                        tempDir,
                        maxT,
                        isHigherRes,
                        isLonger,
                        isSmoother,
                        isFaster,
                        isSlower
                    );

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