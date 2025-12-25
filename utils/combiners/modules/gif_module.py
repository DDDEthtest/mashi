import io
from typing import Tuple

from PIL import Image


def is_gif(data) -> bool:
    return data.startswith(b"GIF87a") or data.startswith(b"GIF89a")


def extract_first_gif_frame(gif_bytes: bytes) -> bytes:
    try:
        with Image.open(io.BytesIO(gif_bytes)) as img:
            img.seek(0)  # first frame

            # Convert to RGB to avoid palette issues
            frame = img.convert("RGB")

            output = io.BytesIO()
            frame.save(output, format="PNG")
            return output.getvalue()
    except Exception as e:
        print(e)


def get_gif_info(image_bytes) -> Tuple[int, float]:
    """
    Returns number of frames and total duration in seconds for a GIF.
    """
    with Image.open(io.BytesIO(image_bytes)) as im:
        num_frames = getattr(im, "n_frames", 1)
        total_duration = 0

        for i in range(num_frames):
            im.seek(i)
            # 'duration' in GIF info is in milliseconds
            frame_duration = im.info.get("duration", 0)
            total_duration += frame_duration / 1000.0

    return num_frames, total_duration


def get_gif_frames_as_bytes(data_bytes):
    """
    Returns a list of PNG bytes for each frame of a GIF.
    Normalizes each frame to full canvas size using disposal method logic.
    """
    with Image.open(io.BytesIO(data_bytes)) as im:
        frames_bytes = []
        num_frames = getattr(im, "n_frames", 1)
        canvas_size = im.size

        # Persistent canvas to accumulate layers (mimics 'body' visibility)
        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        prev_canvas = None

        for i in range(num_frames):
            im.seek(i)

            # GIF disposal methods:
            # 0 or 1: Draw over previous (None/Keep)
            # 2: Restore to background (Clear area)
            # 3: Restore to previous (Revert canvas)
            disposal = im.disposal_method if hasattr(im, "disposal_method") else 0

            if disposal == 3:
                prev_canvas = canvas.copy()

            # Convert current frame to RGBA
            frame_rgba = im.convert("RGBA")

            # Standard GIFs often have localized 'patches' via internal offsets
            # but Pillow's .convert("RGBA") usually normalizes the frame size.
            # We use alpha_composite to ensure transparency doesn't stack 'dirty' edges.
            canvas.alpha_composite(frame_rgba)

            # Snapshot the full canvas
            out = io.BytesIO()
            canvas.copy().save(out, format="PNG")
            frames_bytes.append(out.getvalue())

            # Handle Disposal for the next frame
            if disposal == 2:
                # Clear canvas to transparent
                canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
            elif disposal == 3 and prev_canvas:
                canvas = prev_canvas.copy()

        return frames_bytes