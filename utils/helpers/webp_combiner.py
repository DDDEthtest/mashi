import io

import cairosvg
from PIL import Image

from data.models.traits_info import TraitsInfo
from utils.helpers.apng_helper import check_if_apng, get_apng_info, get_frames_as_bytes
from utils.helpers.math_helper import lcm_of_list
from utils.helpers.svg_helper import remove_redundant_info

resample_mode = Image.Resampling.LANCZOS


def _is_svg(trait):
    return type(trait) is str and "<svg" in trait.lower()

def _svg_bytes_to_img(svg_bytes, target_size=None):
    svg_bytes = remove_redundant_info(svg_bytes)
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes)

    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    if target_size:
        img = img.resize(target_size, resample=resample_mode)

    return img


def get_combined_webp(
        sorted_traits: list,
        bg_size=(552, 736),
        overlay_size=(380, 600),
        is_minted=False
):
    if not sorted_traits:
        raise ValueError("No traits found")

    traits_info = []
    total_ts = []
    imgs_frames = []

    for trait in sorted_traits:
        is_apng = check_if_apng(trait)
        if is_apng:
            num_frames, total_duration = get_apng_info(trait)
            traits_info.append(
                TraitsInfo(
                    frames=num_frames,
                    frame_t=total_duration/num_frames,
                    total_t=total_duration,
                    is_animated=True
                )
            )
            total_ts.append(total_duration)
        else:
            traits_info.append(
                TraitsInfo(
                    frames=1,
                    frame_t=0.1,
                    total_t=0.1,
                    is_animated=False
                )
            )
            total_ts.append(0.1)

    total_t_lcm = lcm_of_list(total_ts)
    print(f"Total Traits LCM: {total_t_lcm}")

    for index, trait_info in enumerate(traits_info):
        if trait_info.is_animated:
            img_frames = get_frames_as_bytes(sorted_traits[index])
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


    for frames in imgs_frames:
        print(len(frames))

    imgs = []

    for sorted_traits in zip(*imgs_frames):
        sorted_traits = list(sorted_traits)  # convert tuple to list

        bg_trait = sorted_traits[0]
        base = Image.open(io.BytesIO(bg_trait)).convert("RGBA")
        base = base.resize(bg_size, resample=resample_mode)

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

        output_bytes = io.BytesIO()
        base.save(output_bytes, format="PNG")
        imgs.append(output_bytes.getvalue())

    # Convert PNG bytes to PIL Images
    webp_frames = [Image.open(io.BytesIO(png)).convert("RGBA") for png in imgs]  # keep RGBA for transparency

    output_webp_bytes = io.BytesIO()
    webp_frames[0].save(
        output_webp_bytes,
        format='WEBP',
        save_all=True,
        append_images=webp_frames[1:],
        duration=100,  # duration per frame in ms
        loop=0,  # 0 = infinite loop
        method=6,  # higher quality compression
        lossless=True  # preserve exact colors
    )

    webp_bytes = output_webp_bytes.getvalue()
    return webp_bytes
