import io
from PIL import Image


def is_gif(data: bytes) -> bool:
    return data.startswith(b"GIF87a") or data.startswith(b"GIF89a")


def extract_first_gif_frame(data: bytes) -> bytes:
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


def get_gif_duration(data: bytes) -> float:
    with Image.open(io.BytesIO(data)) as im:
        num_frames = getattr(im, "n_frames", 1)
        total_duration = 0

        for i in range(num_frames):
            im.seek(i)

            frame_duration = im.info.get("duration", 0)
            total_duration += frame_duration / 1000.0

    return total_duration
