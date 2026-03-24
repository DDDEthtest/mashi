import io
from apng import APNG


def is_png(data: bytes) -> bool:
    return data.startswith(b'\x89PNG\r\n\x1a\n')

def is_apng(data: bytes) -> bool:
    try:
        buffer = io.BytesIO(data)
        im = APNG.open(buffer)

        return len(im.frames) > 1
    except Exception as e:
        print(e)
        return False


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
