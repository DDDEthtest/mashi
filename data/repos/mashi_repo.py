import asyncio

from primary.combiner.pngs.combiners.png_combiner import PngCombiner
from combiner.utils.modules.apng_module import is_png, is_apng
from combiner.utils.modules.gif_module import is_gif
from combiner.utils.modules.webp_module import is_webp
from configs.img_config import LAYER_ORDER
from data.models.download_type import DownloadType
from data.models.image_type import ImageType
from data.models.mashup_error import MashupError
from data.postgres.daos.image_dao import ImageDao
from data.remote.images_api import ImagesApi
from primary.combiner.gifs.services.gif_bridge_service import GifBridgeService
from combiner.utils.modules.svg_module import replace_svg_colors, is_svg

from utils.helpers.image_helper import get_image_type


class MashiRepo:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            _images_api = ImagesApi()
            cls._instance = MashiRepo(_images_api)
        return cls._instance

    def __init__(self, images_api: ImagesApi):
        self._png_combiner = PngCombiner()
        self._image_dao = ImageDao()
        self._images_api = images_api

    def _get_asset(self, asset, colors):
        try:
            name = asset.get("name").lower()
            image_url = asset.get("image")

            data = self._image_dao.get_image(image_url)
            if data is None:
                data = self._images_api.get_image_src(image_url)

                image_type = get_image_type(data)
                if image_type is not ImageType.UNKNOWN:
                    self._image_dao.add_image(image_url, data)

            image_type = get_image_type(data)
            if image_type is ImageType.SVG:
                data = replace_svg_colors(
                    data,
                    body_color=colors.get("base"),
                    eyes_color=colors.get("eyes"),
                    hair_color=colors.get("hair"),
                )

            return name, data

        except Exception as e:
            print(e)
            return None

    async def get_composite(self, mashup: dict, download_type: DownloadType = DownloadType.PNG) -> bytes | MashupError:
        try:
            assets = mashup.get("assets", [])
            colors = mashup.get("colors", {})

            if not assets:
                return MashupError(error_msg="No saved mashup")

            # Get assets in parallel
            tasks = [asyncio.to_thread(self._get_asset, asset, colors) for asset in assets]
            results = await asyncio.gather(*tasks)

            srcs = {}
            for result in results:
                if result:
                    name, src = result
                    srcs[name] = src

            # Filter and order traits based on LAYER_ORDER
            traits = [srcs[name] for name in LAYER_ORDER if name in srcs]

            if download_type is DownloadType.PNG:
                data: bytes = self._png_combiner.get_combined_img_bytes(traits)
            else:
                data: bytes = await GifBridgeService.get_instance().generate_gif(traits)

            if data:
                return data

            raise Exception("Failed to generate composite image")

        except Exception as e:
            print(f"Error in get_composite: {e}")
            return MashupError(error_msg="Internal error. We're working on fix", data=mashup)
