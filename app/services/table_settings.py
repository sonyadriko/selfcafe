import json
import os

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "..", "table_settings.json")

def get_num_tables() -> int:
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f).get("num_tables", 10)
    except (FileNotFoundError, json.JSONDecodeError):
        return 10

def set_num_tables(num: int) -> None:
    try:
        with open(SETTINGS_PATH, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data["num_tables"] = num
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=4)
