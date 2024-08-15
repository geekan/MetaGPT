import json
import os


def save_json_to_file(json_data, filename="json_plan.json"):
    with open(filename, "w") as f:
        json.dump(json_data, f, indent=4)
    print(f"JSON plan saved to {filename}")


def load_json_from_file(filename="json_plan.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    else:
        print(f"No file found at {filename}")
        return None
