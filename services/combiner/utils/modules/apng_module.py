import io

from apng import APNG




def is_apng(image_bytes):
    try:
        buffer = io.BytesIO(image_bytes)
        im = APNG.open(buffer)

        return len(im.frames) > 1
    except Exception as e:
        print(e)
        return False


def get_apng_t(image_bytes) -> float:
    """
    Returns number of frames, total duration in seconds
    """
    im = APNG.open(io.BytesIO(image_bytes))
    total_duration = 0

    for png, control in im.frames:
        if control:
            # Duration in seconds = delay / delay_den
            # If delay_den is 0, it defaults to 100 per spec
            denom = control.delay_den if control.delay_den != 0 else 100
            total_duration += control.delay / denom

    return total_duration
