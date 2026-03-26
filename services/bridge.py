import base64
import uuid
import httpx

from configs.remote_config import PROJECT_ROOT
from configs.server_config import GIF_MAKER_SERVER_URI
from utils.files import save_file, read_file, rm_dir
from utils.helpers.mime_helper import get_mime
from utils.helpers.traits_helper import get_durations


class GifBridgeService:
    _instance = None

    def __init__(self):
        if GifBridgeService._instance is not None:
            raise Exception("This class is a singleton! Use GifService.get_instance()")

        temp_dir = PROJECT_ROOT / "temp"
        temp_dir.mkdir(exist_ok=True, parents=True)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def generate_gif(self, traits: list):
        gif_bytes = None
        temp_dir = PROJECT_ROOT / "temp"
        id_dir = temp_dir / str(uuid.uuid4())

        total_ts = await get_durations(traits)
        max_t = max(total_ts) if total_ts else 0

        id_dir.mkdir(exist_ok=True, parents=True)
        for index, data in enumerate(traits):
            mime = get_mime(data)
            b64 = base64.b64encode(data).decode("utf-8")

            # Save as trait_0, trait_1, etc.
            file_path = id_dir / str(index)
            save_file(file_path, f"data:{mime};base64,{b64}".encode("utf-8"))

        # Construct payload based on format
        payload = {
            "temp_dir": str(id_dir),
            "max_t": max_t,
        }

        async with httpx.AsyncClient(timeout=None) as client:
            try:
                response = await client.post(GIF_MAKER_SERVER_URI, json=payload)
                if response.status_code == 200:
                    result_path = response.text.strip()
                    gif_bytes = read_file(result_path)
                else:
                    print(f"❌ Service Error: {response.status_code}")
            except Exception as e:
                print(f"❌ Connection Error: {e}")

        rm_dir(id_dir)
        return gif_bytes
