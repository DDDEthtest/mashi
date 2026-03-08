const {chromium} = require('playwright');
const path = require('path');
const fs = require('fs');
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

async function generateApng(tempDir, t, isHigherRes = false, isLonger = false, isSmoother = false, isFaster = false, isSlower = false) {

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



    if (isLonger) maxT *= 2;



    if (isSmoother && !(isFaster || isSlower)) {

        captureMs /= 2;

        captFps *= 2;

        playFps *= 2;

        playFps = Math.round(playFps * 100) / 100;

        captFps = Math.round(captFps * 100) / 100;

    }



    if (isFaster) playFps *= 2;

    if (isSlower) playFps /= 2;



    playFps = Math.round(playFps * 100) / 100;



    // --- PRE-CALCULATION FOR VIEWPORT ---

    const tempContext = await browser.newContext({ viewport: { width: gifWidth, height: gifHeight } });

    const tempPage = await tempContext.newPage();

    const imageUrls = await readFilesAsStrings(tempDir);

    imageUrls.shift();



    await tempPage.setContent(`

        <body style="margin:0; background:transparent;">

            ${imageUrls.map(url => `<img src="${url}" style="position:absolute; width:${gifWidth}px; height:${gifHeight}px;" />`).join('')}

        </body>

    `);



    const cropDimensions = await tempPage.evaluate(async ({ w, h }) => {

        const canvas = new OffscreenCanvas(w, h);

        const ctx = canvas.getContext('2d');

        const imgs = Array.from(document.querySelectorAll('img'));

        await Promise.all(imgs.map(img => img.complete ? Promise.resolve() : new Promise(r => img.onload = r)));

        imgs.forEach(img => ctx.drawImage(img, 0, 0, w, h));

        const data = ctx.getImageData(0, 0, w, h).data;

        let topVisibleRow = 0;

        for (; topVisibleRow < h; topVisibleRow++) {

            let isTransparent = true;

            for (let x = 0; x < w; x++) {

                if (data[(topVisibleRow * w + x) * 4 + 3] !== 0) { isTransparent = false; break; }

            }

            if (!isTransparent) break;

        }

        const cropSize = Math.max(1, Math.round(-1.0975 * topVisibleRow + w));

        return { width: cropSize, height: cropSize };

    }, { w: gifWidth, h: gifHeight });



    await tempContext.close();



    const context = await browser.newContext({

        viewport: { width: cropDimensions.width, height: cropDimensions.height }

    });



    try {

        if (maxT < limitT) {

            maxT = Math.ceil(limitT / maxT) * maxT;

        }



        const totalFrames = Math.ceil(maxT * captFps);

        const resourcesDir = tempDir;



        const htmlContent = `

        <html>

          <body style="margin:0; padding:0; background:transparent; overflow:hidden;">

            <div id="crop-box" style="overflow:hidden; position:relative; border-radius:50%; width:${cropDimensions.width}px; height:${cropDimensions.height}px;">

                <div id="stage" style="position:absolute; width:${gifWidth}px; height:${gifHeight}px;">

                    ${imageUrls.map((url, i) => `

                      <div style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; z-index:${i};">

                        <img src="${url}" style="width:100%; height:100%; object-fit:contain;" />

                      </div>

                    `).join('')}

                </div>

            </div>

            <script>

                async function applyCrop() {

                    const w = ${gifWidth};

                    const h = ${gifHeight};

                    const canvas = new OffscreenCanvas(w, h);

                    const ctx = canvas.getContext('2d');

                    const imgs = Array.from(document.querySelectorAll('img'));

                    await Promise.all(imgs.map(img => img.complete ? Promise.resolve() : new Promise(r => img.onload = r)));

                    imgs.forEach(img => ctx.drawImage(img, 0, 0, w, h));

                    const data = ctx.getImageData(0, 0, w, h).data;

                    let topVisibleRow = 0;

                    for (; topVisibleRow < h; topVisibleRow++) {

                        let isTransparent = true;

                        for (let x = 0; x < w; x++) {

                            if (data[(topVisibleRow * w + x) * 4 + 3] !== 0) { isTransparent = false; break; }

                        }

                        if (!isTransparent) break;

                    }

                    const cropSize = Math.max(1, Math.round(-1.0975 * topVisibleRow + w));

                    const cropX = Math.max(0, Math.floor((w - cropSize) / 2));

                    let cropY = topVisibleRow;

                    if (cropY + cropSize > h) cropY = Math.max(0, h - cropSize);



                    const box = document.getElementById('crop-box');

                    const stage = document.getElementById('stage');



                    box.style.width = cropSize + 'px';

                    box.style.height = cropSize + 'px';

                    stage.style.transform = \`translate(-\${cropX}px, -\${cropY}px)\`;

                }

                window.onload = applyCrop;

            </script>

          </body>

        </html>`;



        const midPoint = Math.floor(totalFrames / 2);



        await Promise.all([

            renderFrameRange(context, htmlContent, 0, midPoint, resourcesDir, gifWidth, gifHeight, traitWidth, traitHeight, captureMs),

            renderFrameRange(context, htmlContent, midPoint + 1, totalFrames, resourcesDir, gifWidth, gifHeight, traitWidth, traitHeight, captureMs)

        ]);



        const palettePath = path.join(resourcesDir, 'palette.png');

        const gifPath = path.join(resourcesDir, 'result.gif');



        // Scale to 256x256

        execSync(`ffmpeg -y -threads 0 -i "${path.join(resourcesDir, 'frame_000.png')}" -vf "scale=256:256,palettegen=max_colors=256" "${palettePath}"`);

        execSync(`ffmpeg -y -threads 0 -framerate ${playFps} -i "${resourcesDir}/frame_%03d.png" -i "${palettePath}" -filter_complex "[0:v]scale=256:256,paletteuse=dither=none" "${gifPath}"`);



        return gifPath;

    } catch (e) {

        console.error("Error in generateGif:", e);

        throw e;

    } finally {

        await context.close();

    }

}

module.exports = {
    generateGif,
    generateApng
};