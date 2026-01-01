import asyncio
import datetime
import io
from math import floor, ceil

from PIL import Image

from utils.combiners.modules.apng_module import (
    get_apng_frames_as_bytes,
    is_apng,
)
from utils.constants import ANIM_STEP
from utils.combiners.modules.gif_module import (
    is_gif,
    get_gif_frames_as_bytes,
)
from utils.combiners.helpers.math_helper import lcm_of_list
from utils.combiners.helpers.traits_helper import get_traits_info
from utils.combiners.combiner import get_combined_img_bytes
from utils.combiners.modules.webp_module import get_webp_frames_as_bytes


# ============================================================
# THREAD LIMITER (GLOBAL, SHARED)
# ============================================================

THREAD_LIMIT = 5
_thread_semaphore = asyncio.Semaphore(THREAD_LIMIT)


async def run_in_limited_thread(func, *args, **kwargs):
    async with _thread_semaphore:
        return await asyncio.to_thread(func, *args, **kwargs)


# ============================================================
# FRAME EXTRACTION PER TRAIT
# ============================================================

async def process_trait_frames(index, sorted_traits, trait_info, total_t_lcm, new_t_lcm):
    trait = sorted_traits[index]
    max_frames = int(total_t_lcm / ANIM_STEP)
    if new_t_lcm != 0.0:
        max_frames = int(new_t_lcm / ANIM_STEP)

    if trait_info.is_animated:
        if is_apng(trait):
            img_frames = await run_in_limited_thread(
                get_apng_frames_as_bytes, trait
            )
        elif is_gif(trait):
            img_frames = await run_in_limited_thread(
                get_gif_frames_as_bytes, trait
            )
        else:  # webp
            img_frames = await run_in_limited_thread(
                get_webp_frames_as_bytes, trait
            )
    else:
        img_frames = [trait]

    # Expand frames based on frame timing
    if trait_info.frame_t > ANIM_STEP:
        repeat_count = round(trait_info.frame_t / ANIM_STEP)
        img_frames = [
            frame for frame in img_frames for _ in range(repeat_count)
        ]

    # Extend frames to match total LCM duration
    if total_t_lcm > trait_info.total_t:
        repeat_factor = ceil(total_t_lcm / trait_info.total_t)
        for i in range(repeat_factor):
            img_frames.extend(img_frames)
            if len(img_frames) >= max_frames:
                img_frames = img_frames[:max_frames]
                return img_frames

    return img_frames


async def generate_frames(sorted_traits, traits_info, total_t_lcm, new_t_lcm):
    tasks = [
        process_trait_frames(
            i, sorted_traits, traits_info[i], total_t_lcm, new_t_lcm
        )
        for i in range(len(sorted_traits))
    ]
    return await asyncio.gather(*tasks)


# ============================================================
# FRAME COMPOSITING
# ============================================================

async def process_frame(i, num_layers, imgs_frames, bg_size, overlay_size, is_minted):
    current_layers = []

    # Check if imgs_frames[j][i] is of the expected type
    for j in range(num_layers):
        layer = imgs_frames[j][i]
        if isinstance(layer, bytes):
            current_layers.append(layer)
        else:
            print(f"Warning: Expected bytes, but found {type(layer)} for imgs_frames[{j}][{i}]")
            # If not bytes, handle the conversion here or raise an error
            #current_layers.append(convert_to_bytes(layer))

    # Proceed with combined image creation
    combined_png_bytes = await asyncio.to_thread(
        get_combined_img_bytes,
        current_layers,
        bg_size=bg_size,
        overlay_size=overlay_size,
        is_minted=is_minted
    )
    frame_img = await asyncio.to_thread(
        Image.open, io.BytesIO(combined_png_bytes)
    )
    frame_img = frame_img.convert("RGBA")
    return frame_img


async def process_all_frames(num_frames, num_layers, imgs_frames, bg_size, overlay_size, is_minted):
    try:
        # Create a list of tasks for all frames
        tasks = [
            process_frame(i, num_layers, imgs_frames, bg_size, overlay_size, is_minted)
            for i in range(num_frames)
        ]

        # Gather the results asynchronously
        pil_frames = await asyncio.gather(*tasks)

        # Filter out any failed frames (None) from the list
        pil_frames = [frame for frame in pil_frames if frame is not None]

        return pil_frames

    except Exception as e:
        print(f"Error processing all frames: {e}")
        return []



# ============================================================
# MAIN ENTRYPOINT
# ============================================================

async def get_combined_anim(
    sorted_traits: list,
    bg_size=(552, 736),
    overlay_size=(380, 600),
    img_type: int = 0,
    is_minted=False,
):
    try:
        if not sorted_traits:
            raise ValueError("No traits found")

        now = datetime.datetime.now().time()
        print(now)

        # 1. Get timing info
        traits_info, total_ts = await get_traits_info(sorted_traits)
        total_t_lcm = lcm_of_list(total_ts)

        new_t_lcm = 0.0
        if total_t_lcm > 4.2:
            new_t_lcm = max(total_ts) * 2

        # 2. Expand trait frames to LCM duration
        imgs_frames = await generate_frames(
            sorted_traits, traits_info, total_t_lcm, new_t_lcm
        )

        num_frames = len(imgs_frames[0])
        num_layers = len(imgs_frames)

        # 3. Composite every frame
        pil_frames = await process_all_frames(
            num_frames,
            num_layers,
            imgs_frames,
            bg_size,
            overlay_size,
            is_minted,
        )

        # 4. Encode animation
        animated_bytes = io.BytesIO()

        if img_type == 1:  # GIF
            pil_frames[0].save(
                animated_bytes,
                format="GIF",
                save_all=True,
                append_images=pil_frames[1:],
                duration=ANIM_STEP * 1000,
                loop=0,
                disposal=2,
                optimize=False,
            )
        else:  # WEBP
            pil_frames[0].save(
                animated_bytes,
                format="WEBP",
                save_all=True,
                append_images=pil_frames[1:],
                duration=ANIM_STEP * 1000,
                loop=0,
                lossless=True,
                method=6,
                disposal=2,
            )

        now = datetime.datetime.now().time()
        print(now)

        return animated_bytes.getvalue()

    except Exception as e:
        print(f"Animation Error: {e}")
        return None
