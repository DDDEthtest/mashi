from data.models.image_type import ImageType
from utils.helpers.image_helper import get_image_type


def get_mime(data: bytes) -> str:
    try:
        image_type = get_image_type(data)

        if image_type == ImageType.SVG:
            return "image/svg+xml"

        if image_type == ImageType.WEBP:
            return "image/webp"

        if image_type == ImageType.GIF:
            return "image/gif"

        return "image/png"

    except Exception as e:
        print(e)
        return "image/png"

