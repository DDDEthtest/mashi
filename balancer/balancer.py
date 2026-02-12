import asyncio
from configs.img_config import MAX_GENERATIONS
from data.remote.images_api import ImagesApi
from data.remote.mashi_api import MashiApi
from data.repos.mashi_repo import MashiRepo


class Balancer:
    _instance = None

    def __init__(self):
        self.mashi_api = MashiApi()
        self.mashi_repo = MashiRepo(images_api=ImagesApi())
        self._composite_semaphore = asyncio.Semaphore(MAX_GENERATIONS)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = Balancer()
        return cls._instance

    async def get_composite(self, wallet: str, img_type: int = 0):
        # Acquire semaphore to limit concurrency
        async with self._composite_semaphore:
            try:
                mashup = self.mashi_api.get_mashi_data(wallet)
                return await self.mashi_repo.get_composite(mashup=mashup, img_type=img_type)

            except Exception as e:
                print(f"Error in get_composite: {e}")
                return None
