import io

from PIL import Image


def is_gif(data) -> bool:
    return data.startswith(b"GIF87a") or data.startswith(b"GIF89a")


def extract_first_gif_frame_as_png(gif_bytes: bytes) -> bytes:
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
        return b""


def get_gif_t(image_bytes) -> float:
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

    return total_duration
