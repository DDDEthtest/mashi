import asyncio
import base64
import uuid

import httpx

from services.entry_point.configs.config import MAX_GIF_GENERATIONS_AT_TIME, GIF_MAKER_SERVER_URI

from services.combiner.utils.helpers.mime_type_helper import get_mime_type
from services.combiner.utils.helpers.traits_helper import get_traits_info
from services.combiner.utils.io.files import read_file, rm_dir, save_file
from services.entry_point.configs.config import PROJECT_ROOT


class GifService:
    _instance = None


    def __init__(self):
        if GifService._instance is not None:
            raise Exception("This class is a singleton! Use GifService.get_instance()")
        self.semaphore = asyncio.Semaphore(MAX_GIF_GENERATIONS_AT_TIME)  # defines max GIF generations at time
        temp_dir = PROJECT_ROOT / "temp"
        temp_dir.mkdir(exist_ok=True, parents=True)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def create_gif(self, traits_bytes: list, loops=1):
        gif_bytes = None
        temp_dir = PROJECT_ROOT / "temp"
        id_dir = temp_dir / str(uuid.uuid4())
        total_ts = await get_traits_info(traits_bytes)
        max_t = max(total_ts)
        print(max_t)

        async with self.semaphore:
            id_dir.mkdir(exist_ok=True, parents=True)
            for index, trait_bytes in enumerate(traits_bytes):
                mime = get_mime_type(trait_bytes)
                b64 = base64.b64encode(trait_bytes).decode("utf-8")

                file_path = id_dir / str(index)
                save_file(file_path, f"data:{mime};base64,{b64}".encode("utf-8"))

            payload = {
                "temp_dir": str(id_dir),
                "max_t": max_t * loops,
            }

            async with httpx.AsyncClient(timeout=666.0) as client:
                try:
                    response = await client.post(GIF_MAKER_SERVER_URI, json=payload)
                    if response.status_code == 200:
                        gif_path = response.content
                        gif_bytes = read_file(gif_path)
                    else:
                        print(f"❌ Service Error: {response.status_code}")
                except Exception as e:
                    print(f"❌ Connection Error: {e}")

            rm_dir(id_dir)
            return gif_bytes
