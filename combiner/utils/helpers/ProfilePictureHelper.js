export const toPngSrc = async (svgString) => {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d", { willReadFrequently: true });

    // 1. Dynamic Size Detection
    const widthMatch = svgString.match(/width="(\d+)"/);
    const heightMatch = svgString.match(/height="(\d+)"/);
    const width = widthMatch ? parseInt(widthMatch[1]) : 600;
    const height = heightMatch ? parseInt(heightMatch[1]) : 600;

    canvas.width = width;
    canvas.height = height;

    // 2. Render SVG
    const v = await Canvg.from(ctx, svgString);
    await v.render();

    const imageData = ctx.getImageData(0, 0, width, height);
    const data = imageData.data;

    // 3. Find top visible row
    let topVisibleRow = 0;
    for (; topVisibleRow < height; topVisibleRow++) {
        let isTransparent = true;
        for (let x = 0; x < width; x++) {
            if (data[(topVisibleRow * width + x) * 4 + 3] !== 0) {
                isTransparent = false;
                break;
            }
        }
        if (!isTransparent) break;
    }

    // 4. Generalized Formula (Relative to current height/width)
    // We replace '600' with 'width' to scale the logic
    const cropWidth = Math.max(1, Math.round(-1.0975 * topVisibleRow + width));
    const cropHeight = cropWidth; // Keep it square

    // 5. Center and Clamp
    const cropX = Math.max(0, Math.floor((width - cropWidth) / 2));
    let cropY = topVisibleRow;

    // Ensure we don't go out of bounds at the bottom
    if (cropY + cropHeight > height) {
        cropY = Math.max(0, height - cropHeight);
    }

    const croppedCanvas = document.createElement("canvas");
    croppedCanvas.width = cropWidth;
    croppedCanvas.height = cropHeight;
    const croppedCtx = croppedCanvas.getContext("2d");

    croppedCtx.drawImage(
        canvas,
        cropX, cropY, cropWidth, cropHeight,
        0, 0, cropWidth, cropHeight
    );

    return croppedCanvas.toDataURL("image/png");
};