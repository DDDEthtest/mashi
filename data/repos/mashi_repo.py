import asyncio

from combiner.pngs.combiners.png_combiner import PngCombiner
from combiner.utils.modules.apng_module import is_png, is_apng
from combiner.utils.modules.gif_module import is_gif
from combiner.utils.modules.webp_module import is_webp
from configs.img_config import LAYER_ORDER
from data.models.mashup_error import MashupError
from data.postgres.daos.image_dao import ImageDao
from data.remote.images_api import ImagesApi
from combiner.gifs.services.gif_bridge_service import GifBridgeService
from combiner.utils.modules.svg_module import replace_colors, is_svg


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

            src = self._image_dao.get_image(image_url)

            if src is None:
                src = self._images_api.get_image_src(image_url)

                is_image = is_png(src) or \
                           is_apng(src) or \
                           is_svg(src) or \
                           is_gif(src) or \
                           is_webp(src)

                if is_image:
                    self._image_dao.add_image(image_url, src)


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

    async def get_composite(self, mashup: dict, img_type=0, is_higher_res: int = False, is_longer: bool = False,
                         is_smoother: bool = False, playback_speed: int = 0) -> bytes | MashupError:
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

            ordered_traits = [srcs[name] for name in LAYER_ORDER if name in srcs]

            if img_type == 0:
                img_bytes = self._png_combiner.get_combined_img_bytes(
                    ordered_traits,
                )
            else:
                if playback_speed == 0:
                    is_faster = False
                    is_slower = False
                elif playback_speed == 1:
                    is_faster = True
                    is_slower = False
                else:
                    is_faster = False
                    is_slower = True

                img_bytes = await GifBridgeService.get_instance().create_gif(ordered_traits, is_higher_res=is_higher_res, is_smoother=is_smoother, is_longer=is_longer, is_faster=is_faster, is_slower=is_slower)

            if img_bytes:
                return img_bytes
            else:
                raise Exception("Failed to generate composite image")

        except Exception as e:
            print(e)
            return MashupError(error_msg="Internal error. We're working on fix", data=mashup)
