import csv
import json
import requests
import sys

BASE_URL = "http://localhost:8000"

def load_csv(filename):
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def seed_relational(mp="masterpassword"):
    print("Reading CSVs...")
    try:
        cats_raw = load_csv("categories.csv")
        apps_raw = load_csv("applications.csv")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # 1. Map Categories: ID -> Name
    cat_map = {} # ID -> Name
    payload_cats = []
    
    for c in cats_raw:
        cid = c['id_categoria']
        cname = c['nombre_categoria']
        cat_map[cid] = cname
        payload_cats.append({
            "name": cname,
            "description": "Imported Category",
            "apps": [] 
        })
    
    # 2. Map Apps to Categories
    # We need to find the dict in payload_cats corresponding to the app's cat_id
    # A bit inefficient but fine for small data (O(N*M)) or we can build a lookup.
    
    # Lookup: Name -> Dict Reference
    cat_lookup = {c["name"]: c for c in payload_cats}

    for a in apps_raw:
        cid = a['id_categoria']
        aname = a['nombre_aplicacion']
        
        cname = cat_map.get(cid)
        if cname and cname in cat_lookup:
            cat_lookup[cname]["apps"].append(aname)
        else:
            print(f"Warning: Category ID {cid} not found for app {aname}")

    # 3. Send to API
    payload = {
        "master_password": mp,
        "categories": payload_cats
    }
    
    print(f"Prepared {len(payload_cats)} categories with apps.")
    
    # Auth Check / Setup if needed (Assuming system is already setup from previous steps)
    # But just in case
    
    print("Sending to API...")
    try:
        res = requests.post(f"{BASE_URL}/import", json=payload)
        if res.status_code == 200:
            print("Success!")
            print(res.json())
        else:
            print(f"Error: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        seed_relational(sys.argv[1])
    else:
        seed_relational()
