import io
from typing import Tuple, List

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


def get_webp_info(image_bytes: bytes) -> Tuple[int, float]:
    """
    Returns number of frames and total duration in seconds for a WebP.
    """
    with Image.open(io.BytesIO(image_bytes)) as im:
        num_frames = getattr(im, "n_frames", 1)
        total_duration = 0.0

        for i in range(num_frames):
            im.seek(i)
            # duration is in milliseconds
            frame_duration = im.info.get("duration", 0)
            total_duration += frame_duration / 1000.0

    return num_frames, total_duration


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