const {chromium} = require('playwright');
const path = require('path');
const {execSync} = require('child_process');
const {
    GIF_WIDTH,
    GIF_HEIGHT,
    TRAIT_WIDTH,
    TRAIT_HEIGHT,
    FRAME_DELAY_MS,
    CAPTURE_FPS,
    PLAYBACK_FPS,
    LENGTH_LIMIT_SEC
} = require("../configs/GifConfig");
const {readFilesAsStrings} = require('../utils/Files');

let browserInstance = null;

async function getBrowser() {
    if (!browserInstance) {
        browserInstance = await chromium.launch({
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-frame-rate-limit',
                '--disable-gpu'
            ]
        });
    }
    return browserInstance;
}

/**
 * Renders a specific range of frames for a GIF
 */
async function renderFrameRange(
    context, htmlContent, startFrame, endFrame, resourcesDir
) {
    const page = await context.newPage();
    await page.setContent(htmlContent);

    // Image padding logic
    await page.evaluate(
        ({GIF_WIDTH, GIF_HEIGHT, TRAIT_WIDTH, TRAIT_HEIGHT}) => {
            const imgs = Array.from(document.images);
            return Promise.all(
                imgs.map(img => img.complete ? Promise.resolve() : new Promise(res => img.onload = res))
            ).then(() => {
                const padX = (GIF_WIDTH - TRAIT_WIDTH) / 2;
                const padY = (GIF_HEIGHT - TRAIT_HEIGHT) / 2;
                document.querySelectorAll('img').forEach(img => {
                    const ratio = img.naturalWidth / img.naturalHeight;
                    if (Math.abs(ratio - 0.75) > 0.01) {
                        img.parentElement.style.padding = `${padY}px ${padX}px`;
                    }
                });
            });
        },
        {GIF_WIDTH, GIF_HEIGHT, TRAIT_WIDTH, TRAIT_HEIGHT}
    );

    const client = await page.context().newCDPSession(page);

    // Fast-forward virtual time to the start frame
    await client.send('Emulation.setVirtualTimePolicy', {
        policy: 'advance',
        budget: startFrame * FRAME_DELAY_MS
    });

    for (let i = startFrame; i <= endFrame; i++) {
        const framePath = path.join(resourcesDir, `frame_${String(i).padStart(3, '0')}.png`);
        await page.screenshot({
            path: framePath,
            type: "png",
            omitBackground: false
        });

        await client.send('Emulation.setVirtualTimePolicy', {
            policy: 'advance',
            budget: FRAME_DELAY_MS
        });
    }
    await page.close();
}

/**
 * Generates a GIF using parallel page rendering and multi-threaded FFmpeg
 */
async function generateGif(tempDir, t) {
    const browser = await getBrowser();

    let maxT = t;
    console.log(maxT)

    const context = await browser.newContext({
        viewport: {width: GIF_WIDTH, height: GIF_HEIGHT}
    });

    try {
        if (maxT < LENGTH_LIMIT_SEC) {
            maxT = Math.ceil(LENGTH_LIMIT_SEC / maxT) * maxT;
        }

        const totalFrames = Math.ceil(maxT * CAPTURE_FPS);
        const imageUrls = await readFilesAsStrings(tempDir);
        const resourcesDir = tempDir;

        const htmlContent = `
        <html>
          <body style="margin:0; width:${GIF_WIDTH}px; height:${GIF_HEIGHT}px; background:transparent; overflow:hidden;">
            ${imageUrls.map((url, i) => `
              <div style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; z-index:${i};">
                <img src="${url}" style="width:100%; height:100%; object-fit:contain;" />
              </div>
            `).join('')}
          </body>
        </html>`;

        // Split frames into two halves
        const midPoint = Math.floor(totalFrames / 2);

        // Run both halves in parallel across two tabs
        await Promise.all([
            renderFrameRange(
                context, htmlContent, 0, midPoint, resourcesDir
            ),
            renderFrameRange(
                context, htmlContent, midPoint + 1, totalFrames, resourcesDir
            )
        ]);

        const palettePath = path.join(resourcesDir, 'palette.png');
        const gifPath = path.join(resourcesDir, 'result.gif');

        execSync(
            `ffmpeg -y -threads 1 ` +
            `-i "${resourcesDir}/frame_%03d.png" ` +
            `-vf "format=rgba,palettegen=max_colors=256" ` +
            `"${palettePath}"`,
            {stdio: "inherit"}
        );

        // FFmpeg: -threads 0 allows use of all available CPU cores
        execSync(
            `ffmpeg -y -threads 1 ` +
            `-i "${resourcesDir}/frame_%03d.png" ` +
            `-i "${palettePath}" ` +
            `-lavfi "[0:v]format=rgba,setpts=PTS-STARTPTS[v];[v][1:v]paletteuse=dither=none" ` +
            `"${gifPath}"`,
            {stdio: "inherit"}
        );

        return gifPath;
    } catch (e) {
        console.error("Error in generateGif:", e);
        throw e;
    } finally {
        await context.close();
    }
}


module.exports = {
    generateGif
};