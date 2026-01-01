import io
from typing import Tuple

import imageio
from PIL import Image, ImageSequence


def is_webp(data: bytes) -> bool:
    """
    Detects whether the given bytes represent a WebP file.
    """
    return data.startswith(b"RIFF") and data[8:12] == b"WEBP"


def extract_first_webp_frame(webp_bytes: bytes) -> bytes:
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


def get_webp_info(image_bytes: bytes) -> tuple[int, float]:
    """
    Improved detection of WebP frames and duration.
    """
    with Image.open(io.BytesIO(image_bytes)) as im:
        num_frames = getattr(im, "n_frames", 1)
        total_duration_ms = 0

        for i in range(num_frames):
            im.seek(i)
            # WebP duration is in milliseconds.
            # If 'duration' is missing, it defaults to 0,
            # but standard players usually treat < 10ms as 100ms.
            d = im.info.get("duration", 0)

            if d == 0 and num_frames > 1:
                d = 100  # Default fallback for animations

            total_duration_ms += d

    return num_frames, total_duration_ms / 1000.0


def get_webp_frames_as_bytes(data_bytes):
    im = Image.open(io.BytesIO(data_bytes))
    frames_bytes = []

    canvas_size = im.size

    for frame in ImageSequence.Iterator(im):
        # Start a fresh canvas for each frame
        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

        # Paste the frame onto the canvas
        frame_rgba = frame.convert("RGBA")
        canvas.paste(frame_rgba, (0, 0), frame_rgba)

        # Save frame to bytes
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        frames_bytes.append(buf.getvalue())

    return frames_bytes
