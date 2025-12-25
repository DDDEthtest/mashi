import io
from typing import Tuple

from PIL import Image
from apng import APNG


def is_apng(image_bytes):
    try:
        buffer = io.BytesIO(image_bytes)
        im = APNG.open(buffer)

        return len(im.frames) > 1
    except Exception as e:
        print(e)
        return False


def get_apng_info(image_bytes) -> Tuple[int, float]:
    """
    Returns number of frames, total duration in seconds
    """
    im = APNG.open(io.BytesIO(image_bytes))
    num_frames = len(im.frames)
    total_duration = 0

    for png, control in im.frames:
        if control:
            # Duration in seconds = delay / delay_den
            # If delay_den is 0, it defaults to 100 per spec
            denom = control.delay_den if control.delay_den != 0 else 100
            total_duration += control.delay / denom

    return num_frames, total_duration


def get_apng_frames_as_bytes(data_bytes):
    im = APNG.open(io.BytesIO(data_bytes))
    frames_bytes = []

    if not im.frames:
        return [data_bytes]

    # Initialize the canvas using the first frame's size
    first_png, _ = im.frames[0]
    first_img = Image.open(io.BytesIO(first_png.to_bytes()))
    canvas_size = first_img.size

    # Keep one persistent canvas so the 'body' of the drone stays visible
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    prev_canvas = None

    for png, control in im.frames:
        # Correct attribute mapping for the 'apng' library:
        # x_offset, y_offset, delay_dep (disposal), blend_op
        x, y = (control.x_offset, control.y_offset) if control else (0, 0)

        # Some versions use delay_dep, others use dep_op.
        # We'll use getattr to safely catch the correct one.
        dep_op = getattr(control, 'delay_dep', getattr(control, 'dep_op', 0))
        blend_op = getattr(control, 'blend_op', 0)

        # Disposal Method 2: Restore to Previous
        if dep_op == 2:
            prev_canvas = canvas.copy()

        patch = Image.open(io.BytesIO(png.to_bytes())).convert("RGBA")

        # 1. Handle Blending (Fixes artifacts/dirty edges)
        if blend_op == 0:
            # SOURCE: Clear the area and replace with the patch
            blank_area = Image.new("RGBA", patch.size, (0, 0, 0, 0))
            canvas.paste(blank_area, (x, y))
            canvas.paste(patch, (x, y))
        else:
            # OVER: Alpha composite the patch
            canvas.alpha_composite(patch, (x, y))

        # 2. Snapshot the FULL canvas (Fixes 'cutting')
        # This ensures the output is always the full drone image
        snapshot_bytes = io.BytesIO()
        canvas.copy().save(snapshot_bytes, format="PNG")
        frames_bytes.append(snapshot_bytes.getvalue())

        # 3. Handle Disposal (Prepares canvas for the NEXT frame)
        if dep_op == 1:
            # Restore to Background: Clear the area just painted
            blank_area = Image.new("RGBA", patch.size, (0, 0, 0, 0))
            canvas.paste(blank_area, (x, y))
        elif dep_op == 2 and prev_canvas:
            # Restore to Previous: Revert the canvas
            canvas = prev_canvas.copy()

    return frames_bytes