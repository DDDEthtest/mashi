const {chromium} = require('playwright');
const path = require('path');
const {execSync} = require('child_process');
const {
    captureFps,
    defaultGifWidth,
    defaultGifHeight,
    frameDelayMs,
    playbackFps,
    defaultTraitWidth,
    defaultTraitHeight,
    limitT
} = require("../../../configs/GifConfig");
const {readFilesAsStrings} = require('../../utils/io/Files');

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
    context, htmlContent, startFrame, endFrame, resourcesDir,
    gifWidth, gifHeight, traitWidth, traitHeight, delayMs
) {
    const page = await context.newPage();
    await page.setContent(htmlContent);

    // Image padding logic
    await page.evaluate(
        ({traitWidth, traitHeight, gifWidth, gifHeight}) => {
            const imgs = Array.from(document.images);
            return Promise.all(
                imgs.map(img => img.complete ? Promise.resolve() : new Promise(res => img.onload = res))
            ).then(() => {
                const padX = (gifWidth - traitWidth) / 2;
                const padY = (gifHeight - traitHeight) / 2;
                document.querySelectorAll('img').forEach(img => {
                    const ratio = img.naturalWidth / img.naturalHeight;
                    if (Math.abs(ratio - 0.75) > 0.01) {
                        img.parentElement.style.padding = `${padY}px ${padX}px`;
                    }
                });
            });
        },
        {traitWidth, traitHeight, gifWidth, gifHeight}
    );

    const client = await page.context().newCDPSession(page);

    // Fast-forward virtual time to the start frame
    await client.send('Emulation.setVirtualTimePolicy', {
        policy: 'advance',
        budget: startFrame * delayMs
    });

    for (let i = startFrame; i <= endFrame; i++) {
        const framePath = path.join(resourcesDir, `frame_${String(i).padStart(3, '0')}.png`);
        await page.screenshot({path: framePath, omitBackground: true});

        await client.send('Emulation.setVirtualTimePolicy', {
            policy: 'advance',
            budget: delayMs
        });
    }
    await page.close();
}

/**
 * Generates a GIF using parallel page rendering and multi-threaded FFmpeg
 */
async function generateGif(tempDir, t, isHigherRes, isLonger, isSmoother, isFaster, isSlower) {
    const browser = await getBrowser();

    let maxT = t;

    let gifWidth = defaultGifWidth;
    let gifHeight = defaultGifHeight;
    let traitWidth = defaultTraitWidth;
    let traitHeight = defaultTraitHeight;

    let captureMs = frameDelayMs;

    let playFps = playbackFps;
    let captFps = captureFps;

    if (isHigherRes) {
        gifHeight *= 2;
        gifWidth *= 2;
        traitWidth *= 2;
        traitHeight *= 2;
    }

    if (isLonger) {
        maxT *= 2;
    }

    if (isSmoother && !(isFaster || isSlower)) {
        captureMs /= 2;
        captFps *= 2;
        playFps *= 2;
        playFps = Math.round(playFps * 100) / 100;
        captFps = Math.round(captFps * 100) / 100;
    }

    if (isFaster) {
        playFps *= 2;
        playFps = Math.round(playFps * 100) / 100;
    }

    if (isSlower) {
        playFps /= 2;
        playFps = Math.round(playFps * 100) / 100;
    }

    const context = await browser.newContext({
        viewport: {width: gifWidth, height: gifHeight}
    });

    try {
        if (maxT < limitT) {
            maxT = Math.ceil(limitT / maxT) * maxT;
        }

        const totalFrames = Math.ceil(maxT * captFps);
        const imageUrls = await readFilesAsStrings(tempDir);
        const resourcesDir = tempDir;

        const htmlContent = `
        <html>
          <body style="margin:0; width:${gifWidth}px; height:${gifHeight}px; background:transparent; overflow:hidden;">
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
                context, htmlContent, 0, midPoint, resourcesDir,
                gifWidth, gifHeight, traitWidth, traitHeight, captureMs
            ),
            renderFrameRange(
                context, htmlContent, midPoint + 1, totalFrames, resourcesDir,
                gifWidth, gifHeight, traitWidth, traitHeight, captureMs
            )
        ]);

        const palettePath = path.join(resourcesDir, 'palette.png');
        const gifPath = path.join(resourcesDir, 'result.gif');

        // FFmpeg: -threads 0 allows use of all available CPU cores
        execSync(
            `ffmpeg -y -threads 0 -i "${path.join(resourcesDir, 'frame_000.png')}" -vf "palettegen=max_colors=256" "${palettePath}"`
        );

        execSync(
            `ffmpeg -y -threads 0 -framerate ${playFps} -i "${resourcesDir}/frame_%03d.png" -i "${palettePath}" -filter_complex "[0:v]paletteuse=dither=none" "${gifPath}"`
        );

        return gifPath;
    } catch (e) {
        console.error("Error in generateGif:", e);
        throw e;
    } finally {
        await context.close();
    }
}

module.exports = {generateGif};