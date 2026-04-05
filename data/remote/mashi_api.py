from typing import Any
import requests


def get_mashup(wallet: str) -> dict[Any, Any]:
    try:
        res = requests.get(f"https://mash-it.io/api/mashers/latest?wallet={wallet}")
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
