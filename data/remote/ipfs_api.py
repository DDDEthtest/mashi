import time
import requests
from typing import Optional
from data.remote.client import api_client


def get_image_src(image_url: str, max_retries: int = 5) -> Optional[bytes]:
    urls_to_try = [
        image_url,
        image_url.replace("ipfs.", "ipfs.filebase.")
    ]

    for url in urls_to_try:
        for attempt in range(max_retries):
            try:
                res = api_client.get(url, timeout=10)

                if res.status_code == 200:
                    return res.content

                if res.status_code == 404:
                    break

            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")

            time.sleep(1)

    return None
