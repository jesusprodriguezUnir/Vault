from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID

from . import models, schemas, database, crypto

app = FastAPI(title="Secure Password Vault v2")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup_event():
    database.wait_for_db()
    models.Base.metadata.create_all(bind=database.engine)

from fastapi.responses import FileResponse

@app.get("/", response_class=FileResponse)
def read_root():
    return FileResponse('static/index.html')

@app.get("/ui", response_class=FileResponse)
def read_ui():
    return FileResponse('static/index.html')

# --- AUTH HELPERS ---
def verify_mp(db: Session, mp: str):
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=400, detail="System not initialized")
    if not crypto.verify_master_password(mp, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid Master Password")
    return user

# --- SETUP ---
@app.post("/setup", response_model=schemas.UserResponse)
def setup_system(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    if db.query(models.User).first():
        raise HTTPException(status_code=400, detail="System already initialized")
    
    salt = crypto.generate_salt()
    pw_hash = crypto.hash_master_password(user.master_password)
    
    db_user = models.User(
        username=user.username,
        password_hash=pw_hash,
        master_key_salt=salt
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- CATEGORIES ---
@app.post("/categories", response_model=schemas.CategoryResponse)
def create_category(cat: schemas.CategoryCreate, db: Session = Depends(database.get_db)):
    verify_mp(db, cat.master_password)
    
    # Check duplicate
    if db.query(models.Category).filter(models.Category.name == cat.name).first():
       raise HTTPException(status_code=400, detail="Category already exists")

    new_cat = models.Category(name=cat.name, description=cat.description)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@app.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(database.get_db)):
    return db.query(models.Category).all()

@app.put("/categories/{cat_id}", response_model=schemas.CategoryResponse)
def update_category(cat_id: UUID, cat: schemas.CategoryBase, master_password: str = Body(...), db: Session = Depends(database.get_db)):
    verify_mp(db, master_password)
    db_cat = db.query(models.Category).filter(models.Category.id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db_cat.name = cat.name
    db_cat.description = cat.description
    db.commit()
    db.refresh(db_cat)
    return db_cat

@app.delete("/categories/{cat_id}")
def delete_category(cat_id: UUID, req: schemas.DeleteRequest, db: Session = Depends(database.get_db)):
    verify_mp(db, req.master_password)
    db_cat = db.query(models.Category).filter(models.Category.id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(db_cat)
    db.commit()
    return {"message": "Category deleted"}

# --- APPLICATIONS ---
@app.post("/applications", response_model=schemas.ApplicationResponse)
def create_application(app_in: schemas.ApplicationCreate, db: Session = Depends(database.get_db)):
    verify_mp(db, app_in.master_password)
    
    # Check category exists
    cat = db.query(models.Category).filter(models.Category.id == app_in.category_id).first()
    if not cat:
        raise HTTPException(status_code=400, detail="Invalid Category ID")

    new_app = models.Application(name=app_in.name, description=app_in.description, category_id=app_in.category_id)
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app

@app.get("/applications", response_model=List[schemas.ApplicationResponse])
def get_applications(category_id: UUID = None, db: Session = Depends(database.get_db)):
    q = db.query(models.Application)
    if category_id:
        q = q.filter(models.Application.category_id == category_id)
    return q.all()

@app.put("/applications/{app_id}", response_model=schemas.ApplicationResponse)
def update_application(app_id: UUID, app_in: schemas.ApplicationUpdate, db: Session = Depends(database.get_db)):
    verify_mp(db, app_in.master_password)
    app = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Verify new category exists if changed
    if app.category_id != app_in.category_id:
         if not db.query(models.Category).filter(models.Category.id == app_in.category_id).first():
             raise HTTPException(status_code=400, detail="Invalid Category ID")

    app.name = app_in.name
    app.description = app_in.description
    app.category_id = app_in.category_id
    db.commit()
    db.refresh(app)
    return app

@app.delete("/applications/{app_id}")
def delete_application(app_id: UUID, req: schemas.DeleteRequest, db: Session = Depends(database.get_db)):
    verify_mp(db, req.master_password)
    db_app = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(db_app)
    db.commit()
    return {"message": "Application deleted"}


# --- PASSWORDS ---
@app.post("/passwords", response_model=schemas.PasswordEntryResponse)
def create_password(pw_in: schemas.PasswordEntryCreate, db: Session = Depends(database.get_db)):
    user = verify_mp(db, pw_in.master_password) # Returns User obj
    
    # Verify App exists
    if not db.query(models.Application).filter(models.Application.id == pw_in.application_id).first():
        raise HTTPException(status_code=400, detail="Invalid Application ID")

    # Encrypt
    master_key = crypto.derive_key(pw_in.master_password, user.master_key_salt)
    ciphertext, nonce = crypto.encrypt_password(pw_in.plaintext_password, master_key)

    new_pw = models.PasswordEntry(
        application_id=pw_in.application_id,
        username=pw_in.username,
        environment=pw_in.environment,
        encrypted_password=ciphertext,
        nonce=nonce
    )
    db.add(new_pw)
    db.commit()
    db.refresh(new_pw)
    return new_pw

@app.get("/applications/{app_id}/passwords", response_model=List[schemas.PasswordEntryResponse])
def get_passwords_for_app(app_id: UUID, db: Session = Depends(database.get_db)):
    """Get metadata only for passwords in an app."""
    return db.query(models.PasswordEntry).filter(models.PasswordEntry.application_id == app_id).all()

@app.post("/passwords/decrypt", response_model=schemas.PasswordEntryDecryptedResponse)
def decrypt_password(
    entry_id: UUID = Body(...), 
    master_password: str = Body(...), 
    db: Session = Depends(database.get_db)
):
    user = verify_mp(db, master_password)
    
    item = db.query(models.PasswordEntry).filter(models.PasswordEntry.id == entry_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Entry not found")

    master_key = crypto.derive_key(master_password, user.master_key_salt)
    
    try:
        plaintext = crypto.decrypt_password(item.encrypted_password, item.nonce, master_key)
    except Exception:
        raise HTTPException(status_code=500, detail="Decryption Failed")
    
    return schemas.PasswordEntryDecryptedResponse(
         id=item.id,
         application_id=item.application_id,
         username=item.username,
         environment=item.environment,
         created_at=item.created_at,
         decrypted_password=plaintext
    )

@app.delete("/passwords/{entry_id}")
def delete_password(entry_id: UUID, req: schemas.DeleteRequest, db: Session = Depends(database.get_db)):
    verify_mp(db, req.master_password)
    item = db.query(models.PasswordEntry).filter(models.PasswordEntry.id == entry_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Password deleted"}

# --- SEED / INIT ---
# Useful for dev
@app.post("/dev/seed")
def seed_data(master_password: str = Body(...), db: Session = Depends(database.get_db)):
    """Create basic structure if empty: Work/Personal Cats and some Apps."""
    user = verify_mp(db, master_password)
    
    if db.query(models.Category).first():
        return {"message": "Data already exists, skipping seed"}

    # Categories
    cat_work = models.Category(name="Work", description="Business accounts")
    cat_pers = models.Category(name="Personal", description="Private stuff")
    db.add_all([cat_work, cat_pers])
    db.commit()
    db.refresh(cat_work)
    
    # Apps
    app1 = models.Application(name="Google Workspace", category_id=cat_work.id)
    app2 = models.Application(name="Slack", category_id=cat_work.id)
    app3 = models.Application(name="Netflix", category_id=cat_pers.id)
# --- IMPORT / EXPORT ---
@app.get("/export", response_model=dict)
def export_data(master_password: str = Body(...), db: Session = Depends(database.get_db)):
    """Export full hierarchy to JSON."""
    verify_mp(db, master_password)
    
    cats = db.query(models.Category).all()
    result = {"categories": []}
    
    for c in cats:
        c_data = {
            "name": c.name,
            "description": c.description,
            "apps": []
        }
        for a in c.applications:
            c_data["apps"].append(a.name) # Simple export for now, or full obj? User asked for structure "to create password of applications", so names are enough to re-create structure.
        result["categories"].append(c_data)
        
    return result

from pydantic import BaseModel

class ImportData(BaseModel):
    master_password: str
    categories: List[dict] # [{"name": "C1", "description": "D1", "apps": ["A1", "A2"]}]

@app.post("/import")
def import_data(data: ImportData, db: Session = Depends(database.get_db)):
    """Bulk create categories and apps from JSON."""
    verify_mp(db, data.master_password)
    
    created_cats = 0
    created_apps = 0
    
    for c_in in data.categories:
        # Find or Create Category
        cat = db.query(models.Category).filter(models.Category.name == c_in["name"]).first()
        if not cat:
            cat = models.Category(
                name=c_in["name"],
                description=c_in.get("description", "")
            )
            db.add(cat)
            db.commit()
            db.refresh(cat)
            created_cats += 1
            
        # Apps
        if "apps" in c_in and isinstance(c_in["apps"], list):
            for app_name in c_in["apps"]:
                 # Check if app exists in this cat
                 if not db.query(models.Application).filter(models.Application.category_id == cat.id, models.Application.name == app_name).first():
                     new_app = models.Application(name=app_name, category_id=cat.id)
                     db.add(new_app)
                     created_apps += 1
            db.commit() # Commit all apps for this cat
            
    return {"message": f"Imported {created_cats} categories and {created_apps} applications."}
