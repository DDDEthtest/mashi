from PIL import Image, ImageSequence
from io import BytesIO


def apng_bytes_to_webp_bytes(apng_bytes: bytes) -> bytes:
    """
    Convert APNG bytes to animated WebP bytes.

    Args:
        apng_bytes (bytes): Input APNG data.

    Returns:
        bytes: Output WebP data.
    """
    # Load APNG from bytes
    im = Image.open(BytesIO(apng_bytes))

    # Prepare output buffer
    webp_bytes_io = BytesIO()

    # Check if the image has multiple frames (animation)
    frames = [frame.copy() for frame in ImageSequence.Iterator(im)]
    durations = [frame.info.get("duration", 100) for frame in ImageSequence.Iterator(im)]

    # Save as animated WebP
    frames[0].save(
        webp_bytes_io,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0
    )

    return webp_bytes_io.getvalue()