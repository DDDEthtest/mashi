import asyncio
import queue
import httpx

from configs.config import GENERATOR1_BASE_URL, GENERATOR_PORT, GENERATOR2_BASE_URL, \
    GENERATOR3_BASE_URL
from data.remote.mashi_api import MashiApi


class Balancer:
    _instance = None
    png_queue = asyncio.Queue()
    gif_queue = asyncio.Queue()

    # 1, 2, 3 ... png, gif
    status = [[False, False], [False, False], [False, False]]

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = Balancer()
            cls.mashi_api = MashiApi()
        return cls._instance

    async def get_img(self, payload: dict, post_uri: str, route: str):
        async with httpx.AsyncClient(timeout=666.0) as client:
            try:
                response = await client.post(f"{post_uri}:{GENERATOR_PORT}/{route}", json=payload)
                if response.status_code == 200:
                    return await response.aread()
                else:
                    print(f"❌ Service Error: {response.status_code}")
            except Exception as e:
                print(f"❌ Connection Error: {e}")

    async def png_worker(self):
        while True:
            task_data = await self.png_queue.get()
            payload = task_data.get("payload")
            callback = task_data.get("callback")

            try:
                if not self.status[task_data[0]][task_data[0]]:
                    self.status[task_data[0]][task_data[0]] = True
                    img_bytes = await self.get_img(payload, GENERATOR1_BASE_URL, "png")
                    self.status[task_data[0]][task_data[0]] = False
                    await callback(img_bytes)

                if not self.status[task_data[1]][task_data[0]]:
                    self.status[task_data[1]][task_data[0]] = True
                    img_bytes = await self.get_img(payload, GENERATOR2_BASE_URL, "png")
                    self.status[task_data[1]][task_data[0]] = False
                    await callback(img_bytes)

                if not self.status[task_data[2]][task_data[0]]:
                    self.status[task_data[2]][task_data[0]] = True
                    img_bytes = await self.get_img(payload, GENERATOR3_BASE_URL, "png")
                    self.status[task_data[2]][task_data[0]] = False
                    await callback(img_bytes)

            finally:
                self.png_queue.task_done()

    async def gif_worker(self):
        while True:
            task_data = await self.gif_queue.get()
            payload = task_data.get("payload")
            callback = task_data.get("callback")

            try:
                if not self.status[task_data[0]][task_data[1]]:
                    self.status[task_data[0]][task_data[1]] = True
                    img_bytes = await self.get_img(payload, GENERATOR1_BASE_URL, "gif")
                    self.status[task_data[0]][task_data[1]] = False
                    await callback(img_bytes)

                if not self.status[task_data[1]][task_data[1]]:
                    self.status[task_data[1]][task_data[1]] = True
                    img_bytes = await self.get_img(payload, GENERATOR2_BASE_URL, "gif")
                    self.status[task_data[1]][task_data[1]] = False
                    await callback(img_bytes)

                if not self.status[task_data[2]][task_data[1]]:
                    self.status[task_data[2]][task_data[1]] = True
                    img_bytes = await self.get_img(payload, GENERATOR3_BASE_URL, "gif")
                    self.status[task_data[2]][task_data[1]] = False
                    await callback(img_bytes)
            finally:
                self.gif_queue.task_done()

    async def start_workers(self):
        for i in range(3):
            asyncio.create_task(self.png_worker())
            asyncio.create_task(self.gif_worker())

    async def get_composite(self, wallet: str, img_type: int = 0):
        try:
            data = self.mashi_api.get_mashi_data(wallet)

            async def callback(result):
                return result

            if img_type == 0:
                return await self.png_queue.put({
                    "payload": data,
                    "callback": callback
                })
            else:
                return await self.gif_queue.put({
                    "payload": data,
                    "callback": callback
                })
        except Exception as e:
            return e
