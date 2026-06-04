import asyncio
from configs.img_config import MAX_GENERATIONS
from data.models.download_type import DownloadType
from data.remote.mashit_api import get_mashup
from data.repos.mashi_repo import get_composite_async

_composite_semaphore = asyncio.Semaphore(MAX_GENERATIONS)


async def request_composite_async(wallet: str = None, json = None, download_type: DownloadType = DownloadType.PNG, minted_name: str = None):
    async with _composite_semaphore:
        try:
            if wallet is not None:
                mashup = get_mashup(wallet)
            elif json is not None:
                mashup = json
            else:
                return None

            return await get_composite_async(
                mashup=mashup,
                download_type=download_type,
                minted_name=minted_name
            )

        except Exception as e:
            print(f"❌ Balancer Error: {e}")
            return None
