const puppeteer = require('puppeteer');
const path = require('path');
const {execSync} = require('child_process');
const {
    captureFps,
    defaultGifWidth,
    defaultGifHeight,
    frameDelayMs,
    playbackFps,
    defaultTraitWidth,
    defaultTraitHeight
} = require("../configs/Config");
const {readFilesAsStrings} = require('../utils/io/Files');

let browser;

async function startBrowser() {
    browser = await puppeteer.launch({
        headless: "new",
        executablePath: '/usr/bin/chromium-browser',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-frame-rate-limit',
            '--disable-gpu'
        ]
    });
}

startBrowser();

/**
 * Generates a composited GIF from layered images
 */
async function generateGif(tempDir, maxT) {
    if (maxT < 2) {
        maxT = Math.floor(2 / maxT) * maxT
    }

    const totalFrames = Math.ceil(maxT * captureFps);
    const imageUrls = await readFilesAsStrings(tempDir);
    const resourcesDir = tempDir;

    const context = await browser.createBrowserContext();
    const page = await context.newPage();
    await page.setViewport({width: defaultGifWidth, height: defaultGifHeight});

    const htmlContent = `
  <html>
    <body style="
      margin:0;
      width:${defaultGifWidth}px;
      height:${defaultGifHeight}px;
      background:transparent;
      overflow:hidden;
    ">
      ${imageUrls.map((url, i) => `
        <div style="
          position:absolute;
          inset:0;
          display:flex;
          align-items:center;
          justify-content:center;
          z-index:${i};
        ">
          <img
            src="${url}"
            style="width:100%; height:100%; object-fit:contain;"
          />
        </div>
      `).join('')}
    </body>
  </html>`;

    await page.setContent(htmlContent);

    // ✅ Wait for all images to load + apply correct padding
    await page.evaluate(
        ({defaultTraitWidth, defaultTraitHeight, defaultGifWidth, defaultGifHeight}) => {
            return Promise.all(
                Array.from(document.images).map(img =>
                    img.complete
                        ? Promise.resolve()
                        : new Promise(res => img.onload = res)
                )
            ).then(() => {
                const padX = (defaultGifWidth - defaultTraitWidth) / 2;
                const padY = (defaultGifHeight - defaultTraitHeight) / 2;

                document.querySelectorAll('img').forEach(img => {
                    const ratio = img.naturalWidth / img.naturalHeight;

                    // Only pad non-back traits (not 3:4)
                    if (Math.abs(ratio - 0.75) > 0.01) {
                        // CSS padding order: vertical horizontal
                        img.parentElement.style.padding = `${padY}px ${padX}px`;
                    }
                });
            });
        },
        {defaultTraitWidth, defaultTraitHeight, defaultGifWidth, defaultGifHeight}
    );

    // Freeze time for deterministic capture
    const client = await page.target().createCDPSession();
    await client.send('Emulation.setVirtualTimePolicy', {
        policy: 'advance',
        budget: totalFrames * frameDelayMs
    });

    // Capture frames
    for (let i = 0; i <= totalFrames; i++) {
        const framePath = path.join(
            resourcesDir,
            `frame_${String(i).padStart(3, '0')}.png`
        );

        await page.screenshot({path: framePath, omitBackground: true});

        await client.send('Emulation.setVirtualTimePolicy', {
            policy: 'advance',
            budget: frameDelayMs
        });
    }

    await context.close();

    // FFmpeg
    const palettePath = path.join(resourcesDir, 'palette.png');
    const gifPath = path.join(resourcesDir, 'result.gif');

    try {
        execSync(
            `ffmpeg -y -i "${path.join(resourcesDir, 'frame_000.png')}" -vf "palettegen=max_colors=256" "${palettePath}"`
        );

        execSync(
            `ffmpeg -y -framerate ${playbackFps} -i "${resourcesDir}/frame_%03d.png" -i "${palettePath}" -filter_complex "[0:v]paletteuse=dither=none" "${gifPath}"`
        );

        return gifPath;
    } catch (e) {
        throw e;
    }
}

module.exports = {
    generateGif
};
