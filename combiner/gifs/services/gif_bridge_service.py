import base64
import uuid
import httpx

from configs.config import GIF_MAKER_SERVER_URI
from combiner.utils.helpers.mime_type_helper import get_mime_type
from combiner.utils.helpers.traits_helper import get_traits_info
from combiner.utils.io.files import read_file, rm_dir, save_file
from configs.config import PROJECT_ROOT


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

    async def create_gif(self, traits_bytes: list, is_higher_res: bool = False, is_longer: bool = False,
                         is_smoother: bool = False, is_faster: bool = False, is_slower: bool = False,
                         is_apng: bool = False):
        gif_bytes = None
        temp_dir = PROJECT_ROOT / "temp"
        id_dir = temp_dir / str(uuid.uuid4())

        total_ts = await get_traits_info(traits_bytes)
        max_t = max(total_ts) if total_ts else 0

        id_dir.mkdir(exist_ok=True, parents=True)
        for index, trait_bytes in enumerate(traits_bytes):
            mime = get_mime_type(trait_bytes)
            b64 = base64.b64encode(trait_bytes).decode("utf-8")

            # Save as trait_0, trait_1, etc.
            file_path = id_dir / str(index)
            save_file(file_path, f"data:{mime};base64,{b64}".encode("utf-8"))

        # Construct payload based on format
        payload = {
            "temp_dir": str(id_dir),
            "max_t": max_t,
            "is_apng": is_apng
        }

        # Only add extra flags if we are NOT doing an APNG
        if not is_apng:
            payload.update({
                "is_higher_res": is_higher_res,
                "is_longer": is_longer,
                "is_smoother": is_smoother,
                "is_faster": is_faster,
                "is_slower": is_slower
            })

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
