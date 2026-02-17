import requests
from typing import Dict, Any
from configs.config import MASHIT_BASE_URL, MASHIT_KEY

class MashitApi:
    def __init__(self, base_url: str = MASHIT_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def get_shop_list(self, limit: int, offset: int = 0, api_key: str = MASHIT_KEY) -> Dict[str, Any]:
        params = {"apiKey": api_key, "limit": limit, "offset": offset}
        response = self.session.get(f"{self.base_url}/api/v1/mashers/shop", params=params)
        response.raise_for_status()
        return response.json()

    def get_shop_item(self, item_id: str, api_key: str = MASHIT_KEY) -> Dict[str, Any]:
        params = {"apiKey": api_key}
        response = self.session.get(f"{self.base_url}/api/v1/listings/{item_id}", params=params)
        response.raise_for_status()
        return response.json()