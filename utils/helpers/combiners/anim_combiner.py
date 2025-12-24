import asyncio
import io

from PIL import Image

from utils.helpers.apng.apng_helper import get_apng_frames_as_bytes, is_apng
from utils.helpers.constants import ANIM_STEP
from utils.helpers.gif.gif_helper import is_gif, get_gif_frames_as_bytes
from utils.helpers.math_helper import lcm_of_list
from utils.helpers.traits_helper import get_traits_info
from utils.helpers.combiners.combiner import get_combined_img_bytes
from utils.helpers.webp.webp_helper import get_webp_frames_as_bytes


async def process_trait_frames(index, sorted_traits, trait_info, total_t_lcm):
    trait = sorted_traits[index]

    # Get frames (CPU-bound → offload to thread)
    if trait_info.is_animated:
        if is_apng(trait):
            img_frames = await asyncio.to_thread(get_apng_frames_as_bytes, trait)
        elif is_gif(trait):
            img_frames = await asyncio.to_thread(get_gif_frames_as_bytes, trait)
        else:  # webp
            img_frames = await asyncio.to_thread(get_webp_frames_as_bytes, trait)
    else:
        img_frames = [trait]

    # extend with frame_t
    if trait_info.frame_t > ANIM_STEP:
        repeat_count = round(trait_info.frame_t / ANIM_STEP)
        img_frames = [item for item in img_frames for _ in range(repeat_count)]

    # extend duration to total_t_lcm
    if total_t_lcm > trait_info.total_t:
        repeat_factor = round(total_t_lcm / trait_info.total_t)
        img_frames = img_frames * repeat_factor

    return img_frames

async def generate_frames(sorted_traits, traits_info, total_t_lcm):
    tasks = [
        process_trait_frames(i, sorted_traits, traits_info[i], total_t_lcm)
        for i in range(len(sorted_traits))
    ]
    imgs_frames = await asyncio.gather(*tasks)
    return imgs_frames


async def process_frame(i, num_layers, imgs_frames, bg_size, overlay_size, is_minted):
    current_layers = [imgs_frames[j][i] for j in range(num_layers)]

    # Run CPU-bound function in a separate thread
    combined_png_bytes = await asyncio.to_thread(
        get_combined_img_bytes,
        current_layers,
        bg_size=bg_size,
        overlay_size=overlay_size,
        is_minted=is_minted
    )

    # Convert bytes to PIL image in a thread
    frame_img = await asyncio.to_thread(
        lambda: Image.open(io.BytesIO(combined_png_bytes)).convert("RGBA")
    )
    return frame_img


async def process_all_frames(num_frames, num_layers, imgs_frames, bg_size, overlay_size, is_minted):
    tasks = [
        process_frame(i, num_layers, imgs_frames, bg_size, overlay_size, is_minted)
        for i in range(num_frames)
    ]
    pil_frames = await asyncio.gather(*tasks)
    return pil_frames


async def get_combined_anim(
        sorted_traits: list,
        bg_size=(552, 736),
        overlay_size=(380, 600),
        img_type: int = 0,
        is_minted=False
):
    try:
        if not sorted_traits:
            raise ValueError("No traits found")

        # 2. Get timing and expand frames based on LCM
        traits_info, total_ts = await get_traits_info(sorted_traits)
        total_t_lcm = lcm_of_list(total_ts)
        # imgs_frames is a list of lists: [layer_index][frame_index]
        imgs_frames = await generate_frames(sorted_traits, traits_info, total_t_lcm)

        num_frames = len(imgs_frames[0])
        num_layers = len(imgs_frames)

        # 3. Composite layers for EVERY frame
        # We ensure each frame starts with a clean base

        pil_frames = await process_all_frames(num_frames, num_layers, imgs_frames, bg_size, overlay_size, is_minted)

        # 4. Save with "Complete Redraw" (Disposal Method 2)
        animated_bytes = io.BytesIO()

        if img_type == 1:  # GIF
            # disposal=2 is key: it tells the player to clear the canvas before the next frame
            pil_frames[0].save(
                animated_bytes,
                format='GIF',
                save_all=True,
                append_images=pil_frames[1:],
                duration=100,
                loop=0,
                disposal=2,
                optimize=False
            )
        else:  # WEBP
            pil_frames[0].save(
                animated_bytes,
                format='WEBP',
                save_all=True,
                append_images=pil_frames[1:],
                duration=100,
                loop=0,
                lossless=True,
                method=6,
                disposal=2  # Ensures each frame replaces the previous one entirely
            )

        return animated_bytes.getvalue()

    except Exception as e:
        print(f"Animation Error: {e}")
        return None