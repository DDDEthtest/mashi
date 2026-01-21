import asyncio
import httpx
from configs.config import GENERATOR_PORT, COMBINER_0_IP
from data.remote.mashi_api import MashiApi


class Balancer:
    _instance = None

    def __init__(self):
        self.png_queue = asyncio.Queue()
        self.gif_queue = asyncio.Queue()
        self.extra_queue = asyncio.Queue()
        self.mashi_api = MashiApi()

        # Limit to 10 concurrent get_composite calls
        self._composite_semaphore = asyncio.Semaphore(10)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = Balancer()
        return cls._instance

    async def get_img(self, payload: dict, route: str):
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"http://{COMBINER_0_IP}:{GENERATOR_PORT}/{route}",
                    json=payload
                )
                if response.status_code == 200:
                    return await response.aread()
            except Exception as e:
                print(f"❌ Connection Error: {e}")
        return None

    async def get_composite(self, wallet: str, img_type: int = 0):
        # Acquire semaphore to limit concurrency
        async with self._composite_semaphore:
            try:
                data = self.mashi_api.get_mashi_data(wallet)

                if img_type == 0:
                    return await self.get_img(data, "png")
                elif img_type == 1:
                    return await self.get_img(data, "gif")

            except Exception as e:
                print(f"Error in get_composite: {e}")
                return None
