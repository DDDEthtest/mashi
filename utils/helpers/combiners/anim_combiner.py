import io

from PIL import Image

from utils.helpers.apng.apng_helper import get_apng_frames_as_bytes, is_apng
from utils.helpers.gif.gif_helper import extract_first_frame, is_gif, get_gif_frames_as_bytes
from utils.helpers.math_helper import lcm_of_list
from utils.helpers.traits_helper import get_traits_info
from utils.helpers.combiners.combiner import get_combined_img_bytes


def generate_frames(sorted_traits, traits_info, total_t_lcm):
    imgs_frames = []
    for index, trait_info in enumerate(traits_info):
        if trait_info.is_animated:
            if is_apng(sorted_traits[index]):
                img_frames = get_apng_frames_as_bytes(sorted_traits[index])
            else:
                img_frames = get_gif_frames_as_bytes(sorted_traits[index])
        else:
            img_frames = [sorted_traits[index]]

        # extend with frames
        if trait_info.frame_t > 0.06:
            repeat_count = round(trait_info.frame_t / 0.06)
            img_frames = [item for item in img_frames for _ in range(repeat_count)]

        # extend duration
        if total_t_lcm > trait_info.total_t:
            repeat_factor = round(total_t_lcm / trait_info.total_t)
            img_frames = img_frames * repeat_factor

        imgs_frames.append(img_frames)

    return imgs_frames


def get_combined_anim(
        sorted_traits: list,
        bg_size=(552, 736),
        overlay_size=(380, 600),
        type: int = 0,
        is_test=False,
        is_minted=False
):
    try:
        if not sorted_traits:
            raise ValueError("No traits found")

        # 1. Prepare base traits (Extract static frame if GIF)

        # 2. Get timing and expand frames based on LCM
        traits_info, total_ts = get_traits_info(sorted_traits)
        total_t_lcm = lcm_of_list(total_ts)
        print(total_t_lcm)
        # imgs_frames is a list of lists: [layer_index][frame_index]
        imgs_frames = generate_frames(sorted_traits, traits_info, total_t_lcm)

        num_frames = len(imgs_frames[0])
        num_layers = len(imgs_frames)

        # 3. Composite layers for EVERY frame
        # We ensure each frame starts with a clean base
        pil_frames = []
        for i in range(num_frames):
            current_layers = []
            for j in range(num_layers):
                current_layers.append(imgs_frames[j][i])

            # Get combined bytes (This function handles the alpha_composite)
            combined_png_bytes = get_combined_img_bytes(
                current_layers,
                bg_size=bg_size,
                overlay_size=overlay_size,
                is_minted=is_minted
            )

            # Open as RGBA to preserve transparency for the saving process
            frame_img = Image.open(io.BytesIO(combined_png_bytes)).convert("RGBA")
            pil_frames.append(frame_img)

        # 4. Save with "Complete Redraw" (Disposal Method 2)
        animated_bytes = io.BytesIO()

        if type == 0:  # GIF
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