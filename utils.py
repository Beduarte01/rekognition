import json
import os

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

def save_result(data, filename, folder="results"):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, filename), "w") as f:
        json.dump(data, f, indent=4)