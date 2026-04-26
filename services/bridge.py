import base64
import uuid
import requests
from configs.remote_config import PROJECT_ROOT
from configs.server_config import GIF_MAKER_SERVER_URI
from utils.files import save_file, read_file, rm_dir
from utils.helpers.info_helper import get_durations_async, get_mime


async def generate_gif_async(traits: list):
    gif_bytes = None

    temp_dir = PROJECT_ROOT / "temp"
    temp_dir.mkdir(exist_ok=True, parents=True)

    id_dir = temp_dir / str(uuid.uuid4())
    id_dir.mkdir(exist_ok=True, parents=True)

    total_ts = await get_durations_async(traits)
    max_t = max(total_ts) if total_ts else 0


    for index, data in enumerate(traits):
        mime = get_mime(data)
        b64 = base64.b64encode(data).decode("utf-8")

        # Save as trait_0, trait_1, etc.
        file_path = id_dir / str(index)
        save_file(file_path, f"data:{mime};base64,{b64}".encode("utf-8"))

    payload = {
        "temp_dir": str(id_dir),
        "max_t": max_t,
    }

    try:
        response = requests.post(GIF_MAKER_SERVER_URI, json=payload, timeout=None)

        if response.status_code == 200:
            result_path = response.text.strip()
            gif_bytes = read_file(result_path)
        else:
            print(f"Gif generation failure: {response.status_code}")

    except Exception as e:
        print(e)

    rm_dir(id_dir)
    return gif_bytes
