const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');
const path = require('path');
const {execSync} = require('child_process');
const crypto = require('crypto');

const PORT = 3000;
const gifWidth = 552;
const gifHeight = 736;
const frameDelayMs = 30;
const captureFps = 33.33;
const playbackFps = 30;

let browser;

async function startService() {
    browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-frame-rate-limit', '--disable-gpu']
    });

    http.createServer(async (req, res) => {
        if (req.method === 'POST') {
            let body = '';
            req.on('data', chunk => body += chunk);
            req.on('end', async () => {
                try {
                    const {images, max_t} = JSON.parse(body);
                    const gifBuffer = await generateGif(images, max_t);
                    res.writeHead(200, {'Content-Type': 'image/gif'});
                    res.end(gifBuffer);
                } catch (err) {
                    console.error("Internal Error:", err);
                    res.writeHead(500);
                    res.end(err.message);
                }
            });
        }
    }).listen(PORT, () => {
        // Python listens for this specific string to know the service is ready
        console.log("SERVICE_READY");
    });
}

async function generateGif(imageUrls, maxT) {
    const durationSeconds = maxT;           // 👈 authoritative duration
    const totalFrames = Math.ceil(durationSeconds * captureFps);

    const uniqueId = crypto.randomUUID();
    const framesDir = path.join(__dirname, `frames-${uniqueId}`);
    if (!fs.existsSync(framesDir)) fs.mkdirSync(framesDir);

    // Create an isolated incognito-like window
    const context = await browser.createBrowserContext();
    const page = await context.newPage();
    await page.setViewport({width: gifWidth, height: gifHeight});

    const htmlContent = `
    <html>
      <body style="margin:0; padding:0; width:${gifWidth}px; height:${gifHeight}px; background:transparent; overflow:hidden;">
        ${imageUrls.map((url, i) => `
          <div style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; z-index:${i};">
            <img src="${url}" style="width:100%; height:100%; object-fit:contain;" />
          </div>
        `).join('')}
      </body>
    </html>`;

    await page.setContent(htmlContent);

    // Image logic: Apply padding if aspect ratio isn't 3:4
    await page.evaluate(() => {
        document.querySelectorAll('img').forEach(img => {
            const ratio = img.naturalWidth / img.naturalHeight;
            if (Math.abs(ratio - 0.75) > 0.01) {
                img.parentElement.style.padding = "68px 86px";
            }
        });
    });

    const client = await page.target().createCDPSession();
    await client.send('Emulation.setVirtualTimePolicy', {
        policy: 'advance',
        budget: totalFrames * frameDelayMs
    });

    // Capture Frames
    for (let i = 0; i < totalFrames; i++) {
        const framePath = path.join(framesDir, `frame_${String(i).padStart(3, '0')}.png`);
        await page.screenshot({path: framePath, omitBackground: true});
        await client.send('Emulation.setVirtualTimePolicy', {
            policy: 'advance', budget: frameDelayMs
        });
    }

    await context.close(); // Closes tabs and clears memory

    // FFmpeg Processing
    const palettePath = path.join(framesDir, 'palette.png');
    const gifPath = path.join(framesDir, 'result.gif');

    try {
        // Generate Palette
        execSync(`ffmpeg -y -i "${path.join(framesDir, 'frame_000.png')}" -vf "palettegen=max_colors=256" "${palettePath}"`);
        // Generate Final GIF
        execSync(`ffmpeg -y -framerate ${playbackFps} -i "${framesDir}/frame_%03d.png" -i "${palettePath}" -filter_complex "[0:v]paletteuse=dither=none" "${gifPath}"`);

        const buffer = fs.readFileSync(gifPath);
        fs.rmSync(framesDir, {recursive: true, force: true});
        return buffer;
    } catch (e) {
        fs.rmSync(framesDir, {recursive: true, force: true});
        throw e;
    }
}

startService();