import csv
import io
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from . import models, crypto

def process_csv_import(file_content: bytes, master_password: str, db: Session) -> Tuple[int, int]:
    """
    Parses CSV content (Chrome export or Generic), encrypts passwords, and saves to DB.
    Returns (success_count, error_count).
    
    Supported Columns (Case-insensitive):
    - Chrome: name, url, username, password
    - Generic: category, application, username, password, environment, notes
    """
    # 1. Verify/Prepare User/Keys
    user = db.query(models.User).first()
    if not user:
         raise ValueError("System not initialized")
    
    if not crypto.verify_master_password(master_password, user.password_hash):
        raise ValueError("Invalid Master Password")

    master_key = crypto.derive_key(master_password, user.master_key_salt)

    # 2. Parse CSV
    content_str = file_content.decode('utf-8')
    csv_file = io.StringIO(content_str)
    
    # Sniff header to support different formats more robustly if needed, 
    # but DictReader is usually good enough if we check for column variations.
    reader = csv.DictReader(csv_file)
    
    # Normalize headers to lowercase to handle variations
    if reader.fieldnames:
        reader.fieldnames = [f.lower().strip() for f in reader.fieldnames]

    success_count = 0
    error_count = 0

    # Cache categories and apps to reduce DB queries
    # Key: Name -> ID
    category_cache = {}
    # Key: (CategoryID, AppName) -> ID
    app_cache = {}

    # Pre-populate caches
    for cat in db.query(models.Category).all():
        category_cache[cat.name] = cat.id
        for app in cat.applications:
             app_cache[(cat.id, app.name)] = app.id

    # 3. Process Rows
    for row in reader:
        try:
            # --- Extract Data with Fallbacks ---
            
            # Application Name
            app_name = row.get('name') or row.get('application') or row.get('site_name') or row.get('title')
            
            # Password
            raw_password = row.get('password') or row.get('pass')
            
            # Username
            username = row.get('username') or row.get('user') or row.get('login') or ""

            # URL / Note
            url = row.get('url') or row.get('website') or ""
            note = row.get('note') or row.get('notes') or ""
            full_description = f"{url} {note}".strip()

            # Category - Default to "Imported" if not present
            cat_name = row.get('category') or row.get('group') or "Imported"

            # Environment
            env = row.get('environment') or "Production"

            # Validation
            if not app_name or not raw_password:
                error_count += 1
                continue

            # --- Database Logic ---

            # 1. Get/Create Category
            cat_id = category_cache.get(cat_name)
            if not cat_id:
                new_cat = models.Category(name=cat_name, description="Imported via CSV")
                db.add(new_cat)
                db.flush() # Get ID
                cat_id = new_cat.id
                category_cache[cat_name] = cat_id

            # 2. Get/Create Application
            app_key = (cat_id, app_name)
            app_id = app_cache.get(app_key)
            if not app_id:
                new_app = models.Application(name=app_name, description=full_description, category_id=cat_id)
                db.add(new_app)
                db.flush()
                app_id = new_app.id
                app_cache[app_key] = app_id

            # 3. Create Password Entry
            ciphertext, nonce = crypto.encrypt_password(raw_password, master_key)
            
            # Optional: Check if exact duplicate exists to avoid spamming? 
            # For now, we trust the import action.

            new_pw = models.PasswordEntry(
                application_id=app_id,
                username=username,
                environment=env,
                encrypted_password=ciphertext,
                nonce=nonce
            )
            db.add(new_pw)
            success_count += 1

        except Exception as e:
            # print(f"Error importing row: {e}") 
            error_count += 1
    
    db.commit()
    return success_count, error_count
