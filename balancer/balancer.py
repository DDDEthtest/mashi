import asyncio
from configs.img_config import MAX_GENERATIONS
from data.models.download_type import DownloadType
from data.remote.mashit_api import get_mashup
from data.repos.mashi_repo import get_composite_async

_composite_semaphore = asyncio.Semaphore(MAX_GENERATIONS)


async def request_composite_async(wallet: str, download_type: DownloadType = DownloadType.PNG):
    async with _composite_semaphore:
        try:
            mashup = get_mashup(wallet)

            return await get_composite_async(
                mashup=mashup,
                download_type=download_type
            )

        except Exception as e:
            print(f"❌ Balancer Error: {e}")
            return None
