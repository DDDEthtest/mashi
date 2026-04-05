import asyncio
from data.models.image_type import ImageType
from data.postgres.daos.image_dao import ImageDao
from data.remote.ipfs_api import get_image_src
from data.remote.mashit_api import get_shop_item
from utils.helpers.image_helper import get_image_type


def _format_link(uri: str) -> str:
    if not uri or not uri.startswith("ipfs://"):
        return uri

    return uri.replace("ipfs://", "https://ipfs.io/ipfs/")


async def _cache_async(url: str):
    image_dao = ImageDao()

    try:
        src = await asyncio.to_thread(image_dao.get_image, url)

        if src is None:
            src = await asyncio.to_thread(get_image_src, url)

            image_type = get_image_type(src)

            if image_type is not ImageType.UNKNOWN:
                await asyncio.to_thread(image_dao.add_image, url, src)

    except Exception as e:
        print(e)


async def fetch_and_cache_async(item_id: str):
    try:
        response = await asyncio.to_thread(get_shop_item, item_id)

        listing = response.get("listing", {})
        metadata = listing.get("metadata", {})
        assets = metadata.get("assets", [])

        if not assets:
            return None

        tasks = []
        for asset in assets:
            url = _format_link(asset.get("uri", ""))
            tasks.append(_cache_async(url))

        if tasks:
            await asyncio.gather(*tasks)

    except Exception as e:
        print(e)
