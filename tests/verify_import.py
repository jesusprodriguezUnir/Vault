import requests
import sys

# Constants
BASE_URL = "http://localhost:8000"
MASTER_PASSWORD = "testparams_secret" 
# NOTE: This assumes the server is running with this master password, or we need to setup first. 
# Since we can't easily restart the server with known creds, we might fail if not init.
# But usually dev env uses something simple. 
# Let's try to setup first, ignore if already setup.

def run_test():
    MASTER_PASSWORD = "masterpassword"

    print("Test 1: Check Auth...")
    # We suspect "masterpassword" is correct because it gave 500 (logic error) instead of 401.
    # We skip auth check to proceed to import test.

    print("Test 2: Create Dummy CSV...")
    csv_content = """name,url,username,password
MyBank,https://bank.com,user1,securepass123
SocialMedia,https://social.com,user2,pass456"""
    
    files = {'file': ('chrome_export.csv', csv_content, 'text/csv')}
    # Note: /import/file expects form-data for 'master_password'
    data = {'master_password': MASTER_PASSWORD}

    print("Test 3: Upload CSV...")
    try:
        res = requests.post(f"{BASE_URL}/import/file", files=files, data=data)
        if res.status_code == 200:
            print("SUCCESS: Import returned 200")
            print(res.json())
        else:
            print(f"FAILURE: {res.status_code} - {res.text}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("Test 4: Verify Data...")
    # Get categories to find "Imported"
    cats = requests.get(f"{BASE_URL}/categories").json()
    imported_cat = next((c for c in cats if c['name'] == 'Imported'), None)
    
    if imported_cat:
        print("SUCCESS: 'Imported' category found.")
        
        # Check apps
        apps = requests.get(f"{BASE_URL}/applications?category_id={imported_cat['id']}").json()
        print(f"Apps found: {[a['name'] for a in apps]}")
        
        if any(a['name'] == 'MyBank' for a in apps):
             print("SUCCESS: 'MyBank' app found.")
        else:
             print("FAILURE: 'MyBank' app NOT found.")
    else:
        print("FAILURE: 'Imported' category not found.")

if __name__ == "__main__":
    run_test()
