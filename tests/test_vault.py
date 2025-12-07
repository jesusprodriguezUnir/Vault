from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from app.main import app
from app import database, models, crypto
import os

# --- Test DB Setup ---
# Use in-memory SQLite for speed and isolation during tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[database.get_db] = override_get_db

# Fixture to init DB
@pytest.fixture(scope="module")
def setup_db():
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

client = TestClient(app)

# --- CRYPTO TESTS ---
def test_crypto_hashing():
    password = "supersecretpassword"
    hashed = crypto.hash_master_password(password)
    assert crypto.verify_master_password(password, hashed) is True
    assert crypto.verify_master_password("wrongpassword", hashed) is False

def test_crypto_encryption():
    master_pass = "master"
    salt = crypto.generate_salt()
    key = crypto.derive_key(master_pass, salt)
    
    plaintext = "mysecretdata"
    ciphertext, nonce = crypto.encrypt_password(plaintext, key)
    
    decrypted = crypto.decrypt_password(ciphertext, nonce, key)
    assert decrypted == plaintext

    # Test integrity
    with pytest.raises(Exception):
        crypto.decrypt_password(b'garbage', nonce, key)

# --- API TESTS ---

def test_setup_user(setup_db):
    response = client.post("/setup", json={"username": "admin", "master_password": "masterpassword"})
    assert response.status_code == 200
    assert response.json()["username"] == "admin"

    # Test duplicate setup
    response = client.post("/setup", json={"username": "admin2", "master_password": "mp"})
    assert response.status_code == 400

# Fixture to ensure user exists
@pytest.fixture
def ensure_user():
    client.post("/setup", json={"username": "admin", "master_password": "masterpassword"})

def test_create_and_decrypt_item(setup_db, ensure_user):
    # Create
    item_data = {
        "site_name": "Google",
        "username": "me@gmail.com",
        "plaintext_password": "password123",
        "master_password": "masterpassword", # Correct MP
        "category": "Web",
        "environment": "Production"
    }
    response = client.post("/items", json=item_data)
    assert response.status_code == 200
    item_id = response.json()["id"]
    
    # Decrypt with wrong MP
    response = client.post("/decrypt", json={"entry_id": item_id, "master_password": "wrong"})
    assert response.status_code == 401

    # Decrypt with correct MP
    response = client.post("/decrypt", json={"entry_id": item_id, "master_password": "masterpassword"})
    assert response.status_code == 200
    assert response.json()["decrypted_password"] == "password123"
    assert response.json()["category"] == "Web"

def test_csv_template(setup_db):
    response = client.get("/export/template")
    assert response.status_code == 200
    assert "site_name,username,password,category,environment" in response.text

def test_csv_import(setup_db, ensure_user):
    csv_content = """site_name,username,password,category,environment
Github,gituser,gitpass,Dev,Production
LocalHost,root,toor,Dev,Local
"""
    files = {'file': ('test.csv', csv_content, 'text/csv')}
    data = {'master_password': 'masterpassword'}
    
    response = client.post("/import/csv", files=files, data=data)
    if response.status_code != 200:
        print(response.text)
    assert response.status_code == 200
    assert "Success: 2" in response.json()["message"]

    # Verify Import
    list_resp = client.get("/items")
    items = list_resp.json()
    # Check if items exist (exact count depends on other tests if module scope db)
    assert len(items) >= 2
    
    # Verify content of imported
    github = next(i for i in items if i["site_name"] == "Github")
    assert github["category"] == "Dev"

def test_delete_item(setup_db, ensure_user):
    # 1. Create Item
    item_data = {
        "site_name": "ToDelete",
        "username": "temp",
        "plaintext_password": "pw",
        "master_password": "masterpassword",
        "category": "Tmp",
        "environment": "Test"
    }
    response = client.post("/items", json=item_data)
    assert response.status_code == 200
    item_id = response.json()["id"]

    # 3. Delete with Wrong MP -> Fail 401
    response = client.delete(f"/items/{item_id}", data={"master_password": "wrong"})
    assert response.status_code == 401

    # 4. Delete with Correct MP -> Success
    response = client.delete(f"/items/{item_id}", data={"master_password": "masterpassword"})
    if response.status_code != 200:
        print(f"Delete failed: {response.text}")
    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted successfully"

    # 5. Verify Gone
    response = client.post("/decrypt", json={"entry_id": item_id, "master_password": "masterpassword"})
    assert response.status_code == 404
