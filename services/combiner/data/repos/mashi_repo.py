import asyncio

from data.models.mashup_error import MashupError
from data.remote.images_api import ImagesApi
from gif.gif_service import GifService
from utils.combiner import get_combined_img_bytes
from utils.modules.svg_module import replace_colors, is_svg

layer_order = [
    "background",
    "hair_back",
    "cape",
    "bottom",
    "upper",
    "head",
    "eyes",
    "hair_front",
    "hat",
    "left_accessory",
    "right_accessory",
]


class MashiRepo:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            _images_api = ImagesApi()
            cls._instance = MashiRepo(_images_api)
        return cls._instance

    def __init__(self, images_api: ImagesApi):
        self._images_api = images_api

    def _get_asset(self, asset, colors):
        try:
            name = asset.get("name").lower()
            image_url = asset.get("image")

            src = self._images_api.get_image_src(image_url)

            if is_svg(src):
                src = replace_colors(
                    src,
                    body_color=colors.get("base"),
                    eyes_color=colors.get("eyes"),
                    hair_color=colors.get("hair"),
                )

            return name, src

        except Exception as e:
            print(e)
            return None

    async def get_composite(self, mashup: dict, img_type = 0) -> bytes | MashupError:
        try:
            assets = mashup.get("assets", [])
            colors = mashup.get("colors", {})

            if not assets:
                return MashupError(error_msg="No saved mashup")

            # get assets in parallel
            tasks = [asyncio.to_thread(self._get_asset, asset, colors) for asset in assets]
            results = await asyncio.gather(*tasks)

            srcs = {}
            for result in results:
                if result:
                    name, src = result
                    srcs[name] = src

            ordered_traits = [srcs[name] for name in layer_order if name in srcs]

            if img_type == 0:
                png_bytes = get_combined_img_bytes(
                    ordered_traits,
                )
            else:
                png_bytes = await GifService.get_instance().create_gif(ordered_traits)


            if png_bytes:
                return png_bytes
            else:
                raise Exception("Failed to generate composite image")

        except Exception as e:
            print(e)
            return MashupError(error_msg="Internal error. We're working on fix", data=mashup)
