import asyncio

from services.entry_point.data.firebase.mashers_dao import MashersDao
from services.combiner.data.models.mashup_error import MashupError
from services.combiner.data.remote.images_api import ImagesApi
from services.entry_point.data.remote.mashi_api import MashiApi
from services.combiner.gif.gif_service import GifService
from services.combiner.utils.combiner import get_combined_img_bytes
from services.combiner.utils.modules.svg_module import replace_colors, is_svg

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
            _mashers_dao = MashersDao()
            _mashi_api = MashiApi()
            _images_api = ImagesApi()
            cls._instance = MashiRepo(_mashers_dao, _mashi_api, _images_api)
        return cls._instance

    def __init__(self, mashers_dao: MashersDao, mashi_api: MashiApi, images_api: ImagesApi):
        self._mashers_dao = mashers_dao
        self._mashi_api = mashi_api
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

    async def get_composite(self, wallet: str,
                            img_type: int = 0) -> str | MashupError:
        mashup = None
        try:
            mashup = self._mashi_api.get_mashi_data(wallet)
            assets = mashup.get("assets", [])
            colors = mashup.get("colors", {})

            if not assets:
                return MashupError(error_msg="No saved mashup")

            nft_name = None

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
            elif img_type == 1:
                png_bytes = await GifService.get_instance().create_gif(ordered_traits)
            else:
                png_bytes = await GifService.get_instance().create_gif(ordered_traits, loops=2)

            if png_bytes:
                return png_bytes
            else:
                raise Exception("Failed to generate composite image")

        except Exception as e:
            print(e)
            return MashupError(error_msg="Internal error. We're working on fix", data=mashup)
