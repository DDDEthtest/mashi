from PIL import Image
import io
from configs.img_config import DEFAULT_PNG_WIDTH, DEFAULT_PNG_HEIGHT, DEFAULT_TRAIT_HEIGHT, DEFAULT_TRAIT_WIDTH
from data.models.detailed_trait import DetailedTrait
from data.models.image_type import ImageType
from utils.helpers.image_helper import extract_first_frame, get_image_type
from utils.helpers.svg_helper import convert_svg_to_png

resample_mode = Image.Resampling.LANCZOS


def _convert_to_detailed_traits(traits: list[bytes]) -> list[DetailedTrait]:
    detailed_traits = []
    for i, trait in enumerate(traits):
        temp_bytes = trait
        is_full_size = False

        image_type = get_image_type(trait)

        if image_type is ImageType.GIF or image_type is ImageType.WEBP:
            temp_bytes = extract_first_frame(trait)

        if image_type is ImageType.SVG:
            temp_bytes = convert_svg_to_png(trait)

        if i == 0 or i == len(traits) - 1:
            image = Image.open(io.BytesIO(temp_bytes))
            width, height = image.size
            is_full_size = DEFAULT_PNG_WIDTH / DEFAULT_PNG_HEIGHT == round(width / height, 2)

        detailed_traits.append(DetailedTrait(src=temp_bytes, is_full_size=is_full_size))

    return detailed_traits


def get_combined_png(sorted_traits: list):
    bg_size = (DEFAULT_PNG_WIDTH, DEFAULT_PNG_HEIGHT)
    trait_size = (DEFAULT_TRAIT_WIDTH, DEFAULT_TRAIT_HEIGHT)

    try:
        if not sorted_traits:
            raise ValueError("No traits found")

        detailed_traits = self._convert_to_detailed_traits(sorted_traits)

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
