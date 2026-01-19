import asyncio
import httpx
from configs.config import GENERATOR1_BASE_URL, GENERATOR_PORT, GENERATOR2_BASE_URL, GENERATOR3_BASE_URL
from data.remote.mashi_api import MashiApi


class Balancer:
    _instance = None

    def __init__(self):
        self.png_queue = asyncio.Queue()
        self.gif_queue = asyncio.Queue()
        self.extra_queue = asyncio.Queue()
        self.mashi_api = MashiApi()
        self.urls = [GENERATOR1_BASE_URL, GENERATOR2_BASE_URL, GENERATOR3_BASE_URL]
        # status[server_index][type_index] -> False means available
        self.status = [[False, False], [False, False], [False, False]]

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = Balancer()
        return cls._instance

    async def get_img(self, payload: dict, post_uri: str, route: str):
        async with httpx.AsyncClient(timeout=1200.0) as client:
            try:
                response = await client.post(f"http://{post_uri}:{GENERATOR_PORT}/{route}", json=payload)
                if response.status_code == 200:
                    return await response.aread()
            except Exception as e:
                print(f"❌ Connection Error: {e}")
        return None

    async def _worker(self, q: asyncio.Queue, type_idx: int, route: str):
        while True:
            # task_data is now a dict containing the payload and a Future
            task_data = await q.get()
            payload = task_data["payload"]
            future = task_data["future"]

            for i, url in enumerate(self.urls):
                if not self.status[i][type_idx]:
                    self.status[i][type_idx] = True
                    try:
                        img_bytes = await self.get_img(payload, url, route)
                        if img_bytes:
                            future.set_result(img_bytes)
                            break
                    finally:
                        q.task_done()
                        self.status[i][type_idx] = False



    async def start_workers(self):
        # Start workers once
        for _ in range(3):
            asyncio.create_task(self._worker(self.png_queue, 0, "png"))
            asyncio.create_task(self._worker(self.gif_queue, 1, "gif"))

    async def get_composite(self, wallet: str, img_type: int = 0):
        try:
            data = self.mashi_api.get_mashi_data(wallet)
            loop = asyncio.get_running_loop()
            future = loop.create_future()

            task_item = {"payload": data, "future": future}

            if img_type == 0:
                await self.png_queue.put(task_item)
            elif img_type == 1:
                await self.gif_queue.put(task_item)
            else:
                await self.extra_queue.put(task_item)

            # This waits for the worker to finish and return the bytes
            return await future
        except Exception as e:
            print(f"Error in get_composite: {e}")
