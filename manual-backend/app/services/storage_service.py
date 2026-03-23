import os
import json

BASE_DIR = "manual-storage"
os.makedirs(BASE_DIR, exist_ok=True)

def save_manual(project_id, data):
    folder = os.path.join(BASE_DIR, f"project_{project_id}")
    os.makedirs(folder, exist_ok=True)

    version = len(os.listdir(folder)) + 1
    path = os.path.join(folder, f"v{version}.json")

    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    return version, path