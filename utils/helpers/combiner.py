import io

import cairosvg
from PIL import Image

from utils.helpers.apng_helper import get_apng_frames_as_bytes
from utils.helpers.gif_helper import extract_first_frame, is_gif
from utils.helpers.math_helper import lcm_of_list
from utils.helpers.svg_helper import remove_redundant_info
from utils.helpers.traits_helper import get_traits_info

resample_mode = Image.Resampling.LANCZOS


def _is_svg(trait):
    try:
        return type(trait) is str and "<svg" in trait.lower()
    except Exception as e:
        print(e)
        return False

def _svg_bytes_to_img(svg_bytes, target_size=None):
    try:
        svg_bytes = remove_redundant_info(svg_bytes)

        png_bytes = cairosvg.svg2png(bytestring=svg_bytes.encode("utf-8"))

        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        if target_size:
            img = img.resize(target_size, resample=resample_mode)

        return img
    except Exception as e:
        print(e)


def get_combined_img_bytes(
        sorted_traits: list,
        bg_size=(1104, 1472),
        overlay_size=(760, 1200),
        is_minted=False
):
    print(1)
    if not sorted_traits:
        raise ValueError("No traits found")

    # selecting base img
    bg_trait = sorted_traits[0]
    base = Image.open(io.BytesIO(bg_trait)).convert("RGBA")
    base = base.resize(bg_size, resample=resample_mode)

    for index,trait in enumerate(sorted_traits):
        if is_gif(trait):
            sorted_traits[index] = extract_first_frame(trait)

    minted_trait = None
    if is_minted:
        minted_trait = sorted_traits.pop()

    for layer in sorted_traits[1:]:
        if _is_svg(layer):
            overlay = _svg_bytes_to_img(layer, target_size=overlay_size)
        else:
            overlay = Image.open(io.BytesIO(layer)).convert("RGBA")
            overlay = overlay.resize(overlay_size, resample=resample_mode)

        ow, oh = overlay.size
        x = (base.width - ow) // 2
        y = (base.height - oh) // 2
        base.alpha_composite(overlay, (x, y))

    if minted_trait:
        overlay = _svg_bytes_to_img(minted_trait, target_size=bg_size)
        base.alpha_composite(overlay, (0, 0))

    # get png bytes
    output_bytes = io.BytesIO()
    base.save(output_bytes, format="PNG")
    return output_bytes.getvalue()


def generate_frames(sorted_traits, traits_info, total_t_lcm):
    imgs_frames = []
    for index, trait_info in enumerate(traits_info):
        if trait_info.is_animated:
            img_frames = get_apng_frames_as_bytes(sorted_traits[index])
        else:
            img_frames = [sorted_traits[index]]

        # extend with frames
        if trait_info.frame_t > 0.1:
            repeat_count = round(trait_info.frame_t / 0.1)
            img_frames = [item for item in img_frames for _ in range(repeat_count)]

        # extend duration
        if total_t_lcm > trait_info.total_t:
            repeat_factor = round(total_t_lcm / trait_info.total_t)
            img_frames = img_frames * repeat_factor

        imgs_frames.append(img_frames)

    return imgs_frames


def get_combined_webp(
        sorted_traits: list,
        bg_size=(552, 736),
        overlay_size=(380, 600),
        type: int = 0,
        is_minted=False
):
    if not sorted_traits:
        raise ValueError("No traits found")

    for index, trait in enumerate(sorted_traits):
        if is_gif(trait):
            sorted_traits[index] = extract_first_frame(trait)

    traits_info, total_ts = get_traits_info(sorted_traits)
    total_t_lcm = lcm_of_list(total_ts)
    imgs_frames = generate_frames(sorted_traits, traits_info, total_t_lcm)

    imgs = []
    for sorted_traits in zip(*imgs_frames):
        sorted_traits = list(sorted_traits)  # convert tuple to list
        frame_bytes = get_combined_img_bytes(
            sorted_traits,
            bg_size=bg_size,
            overlay_size=overlay_size
        )
        imgs.append(frame_bytes)

    # Convert PNG bytes to PIL Images
    animated_bytes = io.BytesIO()
    if type == 0:
        gif_frames = [Image.open(io.BytesIO(png)) for png in imgs]
        gif_frames[0].save(
            animated_bytes,
            format='GIF',
            save_all=True,
            append_images=gif_frames[1:],
            duration=100,  # duration of each frame in milliseconds
            loop=0,  # 0 = infinite loop
            disposal=0  # makes frames replace previous ones
        )
    else:
        webp_frames = [Image.open(io.BytesIO(png)).convert("RGBA") for png in imgs]  # keep RGBA for transparency
        webp_frames[0].save(
            animated_bytes,
            format='WEBP',
            save_all=True,
            append_images=webp_frames[1:],
            duration=100,  # duration per frame in ms
            loop=0,  # 0 = infinite loop
            method=6,  # higher quality compression
            lossless=True  # preserve exact colors
        )

    webp_bytes = animated_bytes.getvalue()
    return webp_bytes
