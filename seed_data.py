import requests
import json
import os

BASE_URL = "http://localhost:8000"

def seed(mp="masterpassword"):
    # 0. Load Data
    if not os.path.exists("initial_data.json"):
        print("Error: initial_data.json not found.")
        return

    with open("initial_data.json", "r") as f:
        data = json.load(f)

    # 1. Setup (if needed)
    try:
        requests.post(f"{BASE_URL}/setup", json={"username": "admin", "master_password": mp})
        print("System initialized.")
    except:
        pass 

    # 2. Bulk Import
    payload = {
        "master_password": mp,
        "categories": data["categories"]
    }
    
    print("Importing data... this might take a moment.")
    res = requests.post(f"{BASE_URL}/import", json=payload)
    
    if res.status_code == 200:
        print("Success:", res.json())
    else:
        print("Error:", res.text)

if __name__ == "__main__":
    seed()
