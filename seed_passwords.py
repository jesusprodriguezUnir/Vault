import requests
import json
import random
import string

BASE_URL = "http://localhost:8000"

def generate_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for i in range(length))

def seed_passwords(mp="masterpassword"):
    print("Fetching applications...")
    try:
        res = requests.get(f"{BASE_URL}/applications")
        if res.status_code != 200:
            print("Failed to fetch apps:", res.text)
            return
        apps = res.json()
    except Exception as e:
        print("Error connecting to API:", e)
        return

    print(f"Found {len(apps)} applications. Generating passwords...")
    
    count = 0
    for app in apps:
        # Create a dummy password for each app
        # Only add if it doesn't likely have one (though API allows multiples)
        # We'll just add one.
        
        username = f"{app['name'].lower().replace(' ', '')}_user@example.com"
        password = generate_password()
        
        payload = {
            "application_id": app["id"],
            "username": username,
            "environment": "Production",
            "plaintext_password": password,
            "master_password": mp
        }
        
        r = requests.post(f"{BASE_URL}/passwords", json=payload)
        if r.status_code == 200:
            count += 1
            print(f"[{count}/{len(apps)}] Password added for {app['name']}")
        else:
            print(f"Failed for {app['name']}: {r.text}")

    print(f"Done! Created {count} passwords.")

if __name__ == "__main__":
    seed_passwords()
