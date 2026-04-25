import io

import webp
from PIL import Image
from apng import APNG
from data.models.image_type import ImageType

# Type
def get_image_type(data: bytes) -> ImageType:
    try:
        if b"<svg" in data.lstrip():
            return ImageType.SVG

        if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
            return ImageType.GIF

        if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
            return ImageType.WEBP

        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            if b"acTL" in data:
                return ImageType.APNG
        
        return ImageType.PNG

    except Exception as e:
        print(e)
        return ImageType.UNKNOWN

#
def extract_first_frame(data: bytes) -> bytes:
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.seek(0)

            frame = img.convert("RGBA")
            output = io.BytesIO()
            frame.save(output, format="PNG")

            return output.getvalue()
    except Exception as e:
        print(e)
        return b""


def get_apng_duration(data: bytes) -> float:
    im = APNG.open(io.BytesIO(data))
    total_duration = 0

    for png, control in im.frames:
        if control:
            # Duration in seconds = delay / delay_den
            # If delay_den is 0, it defaults to 100 per spec
            denom = control.delay_den if control.delay_den != 0 else 100
            total_duration += control.delay / denom

    return total_duration


def get_gif_duration(data: bytes) -> float:
    with Image.open(io.BytesIO(data)) as im:
        num_frames = getattr(im, "n_frames", 1)
        total_duration = 0

        for i in range(num_frames):
            im.seek(i)

            frame_duration = im.info.get("duration", 0)
            total_duration += frame_duration / 1000.0

    return total_duration


def get_webp_duration(image_bytes: bytes) -> float:
    try:
        # Load raw bytes into the WebP data structure
        webp_data = webp.WebPData.from_buffer(image_bytes)

        # Initialize the decoder
        dec = webp.WebPAnimDecoder.new(webp_data)

        total_ms = 0
        # Iterate through frames; 'arr' is the image data,
        # 'timestamp_ms' is the cumulative time at the end of that frame.
        for arr, timestamp_ms in dec.frames():
            total_ms = timestamp_ms

        return total_ms / 1000.0
    except Exception as e:
        print(f"Error decoding WebP: {e}")
        return 0.0