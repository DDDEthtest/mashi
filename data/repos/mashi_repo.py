import asyncio
from combiners.pngs.png_combiner import get_combined_png
from configs.img_config import LAYER_ORDER
from data.models.download_type import DownloadType
from data.models.image_type import ImageType
from data.models.mashup_error import MashupError
from data.postgres.daos.image_dao import ImageDao
from data.remote.ipfs_api import get_image_src
from services.bridge import generate_gif_async
from utils.helpers.image_helper import get_image_type
from utils.helpers.svg_helper import replace_svg_colors


def _get_asset(asset, colors):
    try:
        image_dao = ImageDao()

        name = asset.get("name").lower()
        image_url = asset.get("image")

        data = image_dao.get_image(image_url)
        if data is None:
            data = get_image_src(image_url)

            image_type = get_image_type(data)
            if image_type is not ImageType.UNKNOWN:
                image_dao.add_image(image_url, data)

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


async def get_composite_async(mashup: dict, download_type: DownloadType = DownloadType.PNG) -> bytes | MashupError:
    try:
        assets = mashup.get("assets", [])
        colors = mashup.get("colors", {})

        if not assets:
            return MashupError(error_msg="No saved mashup")

        # Get assets in parallel
        tasks = [asyncio.to_thread(_get_asset, asset, colors) for asset in assets]
        results = await asyncio.gather(*tasks)

        srcs = {}
        for result in results:
            if result:
                name, src = result
                srcs[name] = src

        # Filter and order traits based on LAYER_ORDER
        traits = [srcs[name] for name in LAYER_ORDER if name in srcs]

        if download_type is DownloadType.PNG:
            data: bytes = get_combined_png(traits)
        else:
            data: bytes = await generate_gif_async(traits)

        if data:
            return data

        raise Exception("Failed to generate composite image")

    except Exception as e:
        print(e)
        return MashupError(error_msg="Internal error. We're working on fix", data=mashup)
