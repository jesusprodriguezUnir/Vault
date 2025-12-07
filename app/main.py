from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from . import models, schemas, database, crypto, csv_utils

app = FastAPI(title="Secure Password Vault")

# CORS (Allow all for local development simplicity, restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Event: Connect to DB and Create Tables
@app.on_event("startup")
def startup_event():
    # Wait for DB connection
    database.wait_for_db()
    # Create tables
    models.Base.metadata.create_all(bind=database.engine)

# Dependency
def get_db():
    return database.get_db()

# --- API Endpoints ---

@app.post("/setup", response_model=schemas.UserCreate)
def setup_user(user_in: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """Initial setup: Create the main user and master password."""
    # Check if user already exists
    existing_user = db.query(models.User).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already set up.")
    
    salt = crypto.generate_salt()
    pw_hash = crypto.hash_master_password(user_in.master_password)
    
    new_user = models.User(
        username=user_in.username,
        password_hash=pw_hash,
        master_key_salt=salt
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return user_in

@app.get("/items", response_model=List[schemas.PasswordEntryResponse])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    """Get list of password entries (metadata only)."""
    # Check initialization
    if not db.query(models.User).first():
        raise HTTPException(status_code=400, detail="System not initialized")
    
    items = db.query(models.PasswordEntry).offset(skip).limit(limit).all()
    return items

@app.post("/items", response_model=schemas.PasswordEntryResponse)
def create_item(item_in: schemas.PasswordEntryCreate, db: Session = Depends(database.get_db)):
    """Create a new password entry. Requires Master Password to encrypt."""
    # 1. Get user for salt
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=400, detail="System not initialized. Run /setup first.")

    # 2. Verify MP (Authentication)
    if not crypto.verify_master_password(item_in.master_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid Master Password")

    # 3. Derive Key
    master_key = crypto.derive_key(item_in.master_password, user.master_key_salt)

    # 4. Encrypt
    ciphertext, nonce = crypto.encrypt_password(item_in.plaintext_password, master_key)

    # 5. Store
    # 5. Store
    db_item = models.PasswordEntry(
        site_name=item_in.site_name,
        username=item_in.username,
        category=item_in.category,
        environment=item_in.environment,
        encrypted_password=ciphertext,
        nonce=nonce
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.post("/decrypt", response_model=schemas.PasswordEntryDecryptedResponse)
def decrypt_item(request: schemas.PasswordEntryDecryptRequest, db: Session = Depends(database.get_db)):
    """Retrieve and decrypt a password entry."""
    # 1. Get user
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=400, detail="System not initialized.")

    # 2. Verify MP
    if not crypto.verify_master_password(request.master_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid Master Password")

    # 3. Get Items
    item = db.query(models.PasswordEntry).filter(models.PasswordEntry.id == request.entry_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # 4. Derive Key
    master_key = crypto.derive_key(request.master_password, user.master_key_salt)

    # 5. Decrypt
    try:
        plaintext = crypto.decrypt_password(item.encrypted_password, item.nonce, master_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Decryption failed (Data corruption?)")

    return schemas.PasswordEntryDecryptedResponse(
        id=item.id,
        site_name=item.site_name,
        username=item.username,
        category=item.category,
        environment=item.environment,
        created_at=item.created_at,
        decrypted_password=plaintext
    )

@app.get("/export/template", response_class=PlainTextResponse)
def get_csv_template():
    """Download a CSV template for bulk import."""
    return csv_utils.generate_csv_template()

@app.post("/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    master_password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    """Import passwords from a CSV file."""
    try:
        content = await file.read()
        success, errors = csv_utils.process_csv_import(content, master_password, db)
        return {"message": f"Import completed. Success: {success}, Errors: {errors}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error during import")

@app.delete("/items/{item_id}")
def delete_item(item_id: UUID, master_password: str = Form(...), db: Session = Depends(database.get_db)):
    """Delete a password entry. Requires Master Password for authorization."""
    # 1. Verify User exists
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=400, detail="System not initialized")

    # 2. Verify MP
    if not crypto.verify_master_password(master_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid Master Password")

    # 3. Find and Delete
    item = db.query(models.PasswordEntry).filter(models.PasswordEntry.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}

# Serve simple frontend
import os
static_dir = os.path.join(os.path.dirname(__file__), "../static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    print(f"Warning: Static directory not found at {static_dir}")
