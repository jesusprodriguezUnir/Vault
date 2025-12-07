import requests
import json
import uuid

BASE_URL = "http://localhost:8000"
MP = "masterpassword"

def run_test():
    print("--- Starting Edit/Delete Verification ---")
    
    # 1. Create Category
    cat_payload = {"name": f"TestCat_{uuid.uuid4().hex[:6]}", "description": "Original", "master_password": MP}
    res = requests.post(f"{BASE_URL}/categories", json=cat_payload)
    if res.status_code != 200: return print("FAIL: Create Cat", res.text)
    cat = res.json()
    print(f"Created Cat: {cat['name']}")
    
    # 2. Edit Category
    cat['name'] += "_Edited"
    cat['description'] = "Updated Desc"
    cat['master_password'] = MP
    res = requests.put(f"{BASE_URL}/categories/{cat['id']}", json=cat)
    if res.status_code != 200: return print("FAIL: Update Cat", res.text)
    updated_cat = res.json()
    if updated_cat['name'] == cat['name']:
        print("PASS: Category Edit")
    else:
        print("FAIL: Category Edit Name Mismatch")

    # 3. Create App
    app_payload = {"name": f"TestApp_{uuid.uuid4().hex[:6]}", "category_id": cat['id'], "master_password": MP}
    res = requests.post(f"{BASE_URL}/applications", json=app_payload)
    if res.status_code != 200: return print("FAIL: Create App", res.text)
    app = res.json()
    print(f"Created App: {app['name']}")

    # 4. Edit App
    app['name'] += "_Edited"
    app['description'] = "New App Desc"
    app['master_password'] = MP
    res = requests.put(f"{BASE_URL}/applications/{app['id']}", json=app)
    if res.status_code != 200: return print("FAIL: Update App", res.text)
    updated_app = res.json()
    if updated_app['name'] == app['name']:
        print("PASS: App Edit")
    else:
        print("FAIL: App Edit Name Mismatch")

    # 5. Delete App
    payload = {"master_password": MP} # Delete usually sends body in our API
    # requests.delete supports json param
    res = requests.delete(f"{BASE_URL}/applications/{app['id']}", json=payload)
    if res.status_code == 200:
        print("PASS: App Delete")
    else:
        print("FAIL: App Delete", res.text)

    # 6. Delete Category
    res = requests.delete(f"{BASE_URL}/categories/{cat['id']}", json=payload)
    if res.status_code == 200:
        print("PASS: Category Delete")
    else:
        print("FAIL: Category Delete", res.text)

if __name__ == "__main__":
    run_test()
