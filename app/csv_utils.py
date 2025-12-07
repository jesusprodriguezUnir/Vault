import csv
import io
from typing import List, Tuple
from sqlalchemy.orm import Session
from . import models, crypto, schemas

def generate_csv_template() -> str:
    """Generates a CSV template header."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['site_name', 'username', 'password', 'category', 'environment'])
    return output.getvalue()

def process_csv_import(file_content: bytes, master_password: str, db: Session) -> Tuple[int, int]:
    """
    Parses CSV content, encrypts passwords, and saves to DB.
    Returns (success_count, error_count).
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
    reader = csv.DictReader(csv_file)
    
    success_count = 0
    error_count = 0

    # 3. Process Rows
    for row in reader:
        try:
            site = row.get('site_name')
            username = row.get('username')
            password = row.get('password')
            category = row.get('category', 'General')
            environment = row.get('environment', 'Production')

            if not site or not password:
                error_count += 1
                continue

            ciphertext, nonce = crypto.encrypt_password(password, master_key)
            
            db_item = models.PasswordEntry(
                site_name=site,
                username=username,
                category=category,
                environment=environment,
                encrypted_password=ciphertext,
                nonce=nonce
            )
            db.add(db_item)
            success_count += 1
        except Exception:
            error_count += 1
    
    db.commit()
    return success_count, error_count
