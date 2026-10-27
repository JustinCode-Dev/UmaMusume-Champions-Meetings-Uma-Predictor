import json
from pathlib import Path

def data_load(cm_folder, check=False):
    all_data = []
    for folder_path in cm_folder:
        folder = Path("data/raw/input/") / folder_path
        for json_path in sorted(folder.glob("*.json")):
            with open (json_path, "r", encoding="utf-8") as f:
                if check is True:
                    all_data.append({"filename": json_path.name, "data": json.load(f)})
                else:
                    all_data.append(json.load(f))
    return all_data