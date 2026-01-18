// Local server
const PORT = 3001;

// GIFs
const defaultGifWidth = 552 * 1.125;
const defaultGifHeight = 736 * 1.125;
const defaultTraitWidth = 380 * 1.125;
const defaultTraitHeight = 600 * 1.125;

const frameDelayMs = 30;
const captureFps = 33.33;
const playbackFps = 33.33;

module.exports = {
    PORT,
    defaultGifWidth,
    defaultGifHeight,
    defaultTraitWidth,
    defaultTraitHeight,
    frameDelayMs,
    captureFps,
    playbackFps
};