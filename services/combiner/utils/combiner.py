from PIL import Image

import io
from services.entry_point.configs.config import DEFAULT_PNG_WIDTH, DEFAULT_PNG_HEIGHT, DEFAULT_TRAIT_HEIGHT, DEFAULT_TRAIT_WIDTH
from services.combiner.data.models.detailed_trait import DetailedTrait
from services.combiner.utils.modules.gif_module import extract_first_gif_frame_as_png, is_gif
from services.combiner.utils.modules.svg_module import svg_bytes_to_png, is_svg
from services.combiner.utils.modules.webp_module import extract_first_webp_frame_as_png, is_webp

resample_mode = Image.Resampling.LANCZOS


def convert_to_detailed_traits(traits: list[bytes]) -> list[DetailedTrait]:
    detailed_traits = []
    for i, trait in enumerate(traits):
        temp_png_bytes = trait
        is_full_size = False

        if is_gif(trait):
            temp_png_bytes = extract_first_gif_frame_as_png(trait)
        if is_webp(trait):
            temp_png_bytes = extract_first_webp_frame_as_png(trait)
        if is_svg(trait):
            temp_png_bytes = svg_bytes_to_png(trait)

        if i == 0 or i == len(traits) - 1:
            image = Image.open(io.BytesIO(temp_png_bytes))
            width, height = image.size
            is_full_size = DEFAULT_PNG_WIDTH / DEFAULT_PNG_HEIGHT == round(width / height, 2)

        detailed_traits.append(DetailedTrait(src=temp_png_bytes, is_full_size=is_full_size))

    return detailed_traits


def get_combined_img_bytes(
        sorted_traits: list
):
    bg_size = (DEFAULT_PNG_WIDTH, DEFAULT_PNG_HEIGHT)
    trait_size = (DEFAULT_TRAIT_WIDTH, DEFAULT_TRAIT_HEIGHT)

    try:
        if not sorted_traits:
            raise ValueError("No traits found")

        detailed_traits = convert_to_detailed_traits(sorted_traits)

        base = Image.new("RGBA", bg_size, (0, 0, 0, 0))
        for detailed_trait in detailed_traits:
            if detailed_trait.is_full_size:
                pos = (0, 0)
                size = bg_size
            else:
                pos = (
                    int((DEFAULT_PNG_WIDTH - DEFAULT_TRAIT_WIDTH) / 2),
                    int((DEFAULT_PNG_HEIGHT - DEFAULT_TRAIT_HEIGHT) / 2)
                )
                size = trait_size

            img = Image.open(io.BytesIO(detailed_trait.src)).convert("RGBA")
            img = img.resize(size, resample=resample_mode)

            base.alpha_composite(img, pos)

        # get png bytes
        composite_bytes = io.BytesIO()
        base.save(composite_bytes, format="PNG")
        return composite_bytes.getvalue()
    except Exception as e:
        print(e)
