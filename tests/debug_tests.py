from fastapi.testclient import TestClient
from app.main import app
import sys

client = TestClient(app)

def debug_delete():
    print("--- Debugging DELETE ---")
    # 1. Setup
    client.post("/setup", json={"username": "debug", "master_password": "mp"})
    
    # 2. Create Cat
    res = client.post("/categories", json={"name": "DebugCat", "master_password": "mp"})
    if res.status_code != 200:
        print("Setup Cat Failed:", res.text)
        return
    cat_id = res.json()["id"]

    # 3. Delete Cat
    print(f"Attempting to DELETE category {cat_id}")
    res = client.request("DELETE", f"/categories/{cat_id}", json={"master_password": "mp"})
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    debug_delete()
