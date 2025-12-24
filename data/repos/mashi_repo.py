import asyncio

from data.db.daos.mashers_dao import MashersDao
from data.models.mashup_error import MashupError
from data.remote.alchemy_api import AlchemyApi
from data.remote.images_api import ImagesApi
from data.remote.mashi_api import MashiApi
from utils.helpers.combiners.anim_combiner import get_combined_anim
from utils.helpers.combiners.combiner import get_combined_img_bytes
from utils.helpers.generator import generate_minted_svg
from utils.helpers.svg.svg_helper import replace_colors, is_svg
from utils.io.test_data_io import get_test_mashi_data

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
            _alchemy_api = AlchemyApi()
            _images_api = ImagesApi()
            cls._instance = MashiRepo(_mashers_dao, _mashi_api, _alchemy_api, _images_api)
        return cls._instance

    def __init__(self, mashers_dao: MashersDao, mashi_api: MashiApi, alchemy_api: AlchemyApi, images_api: ImagesApi):
        self._mashers_dao = mashers_dao
        self._mashi_api = mashi_api
        self._alchemy_api = alchemy_api
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


    def _check_mint_ownership(self, wallet: str, assets: list, mint: int) -> str | MashupError:
        background_uri = next(
            (item["image"] for item in assets if item["name"] == "background"),
            None
        )
        if not background_uri:
            return MashupError(error_msg=f"You don't have NFT with that mint: #{mint}")

        names = self._alchemy_api.get_available_mints(wallet, background_uri)
        if not names:
            return MashupError(error_msg=f"You don't have NFT with that mint: #{mint}")

        nft_name = next((name for name in names if f"#{mint}" in name), None)
        if not nft_name:
            return MashupError(error_msg=f"You don't have NFT with that mint: #{mint}")

        return nft_name

    async def get_composite(self, wallet: str, mint: int | None = None, is_test = False, img_type: int = 0) -> str | MashupError:
        mashup = None
        try:
            if is_test:
                mashup = get_test_mashi_data()
            else:
                mashup = self._mashi_api.get_mashi_data(wallet)
            assets = mashup.get("assets", [])
            colors = mashup.get("colors", {})

            if not assets:
                return MashupError(error_msg="No saved mashup")

            nft_name = None
            if mint:
                if not is_test:
                    check_res = self._check_mint_ownership(wallet, assets, mint)
                    if type(check_res) is not str:
                        return check_res

                    nft_name = check_res
                if is_test:
                    nft_name = "For testing purpose"

            # get assets in parallel
            tasks = [asyncio.to_thread(self._get_asset, asset, colors) for asset in assets]
            results = await asyncio.gather(*tasks)

            srcs = {}
            for result in results:
                if result:
                    name, src = result
                    srcs[name] = src

            ordered_traits = [srcs[name] for name in layer_order if name in srcs]

            # add minted trait
            if mint:
                ordered_traits.append(generate_minted_svg(nft_name))

            if img_type == 0:
                png_bytes = get_combined_img_bytes(
                    ordered_traits,
                    is_minted=bool(mint),
                )
            else:
                png_bytes = await get_combined_anim(
                    ordered_traits,
                    is_minted=bool(mint),
                    img_type=img_type,
                )

            if png_bytes:
                return png_bytes
            else:
                raise Exception("Failed to generate composite image")

        except Exception as e:
            print(e)
            return MashupError(error_msg="Internal error. We're working on fix", data=mashup)
