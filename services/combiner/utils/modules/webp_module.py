import io

from PIL import Image
import webp


def is_webp(data: bytes) -> bool:
    """
    Detects whether the given bytes represent a WebP file.
    """
    return data.startswith(b"RIFF") and data[8:12] == b"WEBP"


def extract_first_webp_frame_as_png(webp_bytes: bytes) -> bytes:
    """
    Extracts the first frame of a (possibly animated) WebP
    and returns it as PNG bytes.
    """
    try:
        with Image.open(io.BytesIO(webp_bytes)) as img:
            img.seek(0)

            frame = img.convert("RGBA")
            output = io.BytesIO()
            frame.save(output, format="PNG")

            return output.getvalue()
    except Exception as e:
        print(e)
        return b""


def get_webp_t(image_bytes: bytes) -> float:
    """
    Calculates the total duration of a WebP animation from raw bytes
    using the libwebp wrapper.
    """
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
