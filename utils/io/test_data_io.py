import json

def save_test_mashi_data(data: dict):
    try:
        from main import PROJECT_ROOT
        json_str = json.dumps(data, ensure_ascii=False)
        (PROJECT_ROOT / "test_mashi.txt").write_text(json_str, encoding="utf-8")
    except Exception as e:
        print(e)


def get_test_mashi_data():
    try:
        from main import PROJECT_ROOT
        path = PROJECT_ROOT / "test_mashi.txt"

        if not path.exists():
            return {}

        data = json.loads(path.read_text(encoding="utf-8"))

        colors = data.get("colors", {})
        traits = data.get("assets", [])

        return {
            "colors": colors,
            "assets": traits
        }

    except Exception as e:
        print(e)
        return {}