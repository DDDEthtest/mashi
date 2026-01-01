import io

from PIL import Image

from utils.combiners.modules.gif_module import extract_first_gif_frame, is_gif
from utils.combiners.modules.svg_module import svg_bytes_to_img, is_svg
from utils.combiners.modules.webp_module import is_webp, extract_first_webp_frame

resample_mode = Image.Resampling.LANCZOS


def get_combined_img_bytes(
        sorted_traits: list,
        bg_size=(1104, 1472),
        overlay_size=(760, 1200),
        is_minted=False
):
    try:
        if not sorted_traits:
            raise ValueError("No traits found")

        for trait in sorted_traits:
            if not isinstance(trait, bytes):
                raise ValueError(f"Expected a byte object, got {type(trait)}")

        for index, trait in enumerate(sorted_traits):
            if is_gif(trait):
                sorted_traits[index] = extract_first_gif_frame(trait)
            if is_webp(trait):
                sorted_traits[index] = extract_first_webp_frame(trait)

        bg_trait = sorted_traits[0]
        if is_svg(bg_trait):
            base = svg_bytes_to_img(bg_trait, target_size=bg_size)
        else:
            base = Image.open(io.BytesIO(bg_trait)).convert("RGBA")
            base = base.resize(bg_size, resample=resample_mode)

        minted_trait = None
        if is_minted:
            minted_trait = sorted_traits.pop()

        for layer in sorted_traits[1:]:
            if is_svg(layer):
                overlay = svg_bytes_to_img(layer, target_size=overlay_size)
            else:
                overlay = Image.open(io.BytesIO(layer)).convert("RGBA")
                overlay = overlay.resize(overlay_size, resample=resample_mode)

            ow, oh = overlay.size
            x = (base.width - ow) // 2
            y = (base.height - oh) // 2
            base.alpha_composite(overlay, (x, y))

        if minted_trait:
            overlay = svg_bytes_to_img(minted_trait, target_size=bg_size)
            base.alpha_composite(overlay, (0, 0))

        # get png bytes
        output_bytes = io.BytesIO()
        base.save(output_bytes, format="PNG")
        return output_bytes.getvalue()
    except Exception as e:
        print(e)
