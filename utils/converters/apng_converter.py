from PIL import Image, ImageSequence
from io import BytesIO


def convert_apng_to_webp(apng_bytes: bytes) -> bytes:
    im = Image.open(BytesIO(apng_bytes))
    webp_bytes_io = BytesIO()

    frames = [frame.copy() for frame in ImageSequence.Iterator(im)]
    durations = [frame.info.get("duration", 100) for frame in ImageSequence.Iterator(im)]

    frames[0].save(
        webp_bytes_io,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0
    )

    return webp_bytes_io.getvalue()
