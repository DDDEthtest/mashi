import asyncio
from configs.img_config import MAX_GENERATIONS
from data.models.download_type import DownloadType
from data.remote.images_api import ImagesApi
from data.remote.mashi_api import MashiApi
from data.repos.mashi_repo import MashiRepo


class Balancer:
    _instance = None

    def __init__(self):
        self.mashi_api = MashiApi()
        # Initialize MashiRepo via the API as per your structure
        self.mashi_repo = MashiRepo(images_api=ImagesApi())
        self._composite_semaphore = asyncio.Semaphore(MAX_GENERATIONS)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = Balancer()
        return cls._instance

    async def get_composite(self, wallet: str, download_type: DownloadType = DownloadType.PNG):
        async with self._composite_semaphore:
            try:
                # Fetch mashup data (assets, colors) from the API
                mashup = self.mashi_api.get_mashup(wallet)

                # Forward request to MashiRepo
                return await self.mashi_repo.get_composite(
                    mashup=mashup,
                    download_type=download_type
                )

            except Exception as e:
                print(f"❌ Balancer Error: {e}")
                return None