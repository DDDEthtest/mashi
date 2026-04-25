from typing import Dict, Any

from configs.remote_config import MASHIT_KEY, MASHIT_BASE_URL
from data.remote.client import api_client


def get_shop_list(limit: int, offset: int = 0, api_key: str = MASHIT_KEY) -> Dict[str, Any]:
    params = {"apiKey": api_key, "limit": limit, "offset": offset}
    response = api_client.get(f"{MASHIT_BASE_URL}/api/v1/mashers/shop", params=params)
    response.raise_for_status()
    return response.json()


def get_shop_item(item_id: str, api_key: str = MASHIT_KEY) -> Dict[str, Any]:
    params = {"apiKey": api_key}
    response = api_client.get(f"{MASHIT_BASE_URL}/api/v1/listings/{item_id}", params=params)
    response.raise_for_status()
    return response.json()


def get_mashup(wallet: str) -> dict[Any, Any]:
    try:
        res = api_client.get(f"{MASHIT_BASE_URL}api/mashers/latest?wallet={wallet}")
        data = res.json()
        if data.get("message") == "No mashups found":
            return {}

        colors = data.get("colors", {})
        traits = data.get("assets", [])

        return {
            "colors": colors,
            "assets": traits
        }

    except Exception as e:
        print(e)
        return {}
