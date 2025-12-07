import os
import base64
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Configuration
# Salt length for Argon2 is handled by the library by default (16 bytes)
# Nonce length for AES-GCM is standard 12 bytes
NONCE_LENGTH = 12
KEY_LENGTH = 32 # 32 bytes = 256 bits

ph = PasswordHasher()

def generate_salt() -> bytes:
    """Generates a random salt."""
    return os.urandom(16)

def derive_key(master_password: str, salt: bytes) -> bytes:
    """
    Derives a 32-byte (256-bit) AES key from the master password and salt.
    Note: In a production system we might use Argon2 specifically for key derivation (Argon2id KDF),
    Here we use Argon2's hash mechanism but configured to output raw bytes if possible, 
    or we can use standard PBKDF2HMAC. 
    
    However, to keep it simple and robust using the chosen library `argon2-cffi`:
    We will use the Argon2 low-level hash function to get a 32-byte raw hash.
    """
    from argon2.low_level import hash_secret_raw, Type
    
    # Deriving a 32-byte key
    key = hash_secret_raw(
        secret=master_password.encode('utf-8'),
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=KEY_LENGTH,
        type=Type.ID
    )
    return key

def encrypt_password(plaintext: str, master_key: bytes) -> Tuple[bytes, bytes]:
    """
    Encrypts plaintext using AES-256-GCM.
    Returns (ciphertext, nonce).
    Auth Tag is included in the ciphertext by the library normally, or appended.
    cryptography.hazmat.primitives.ciphers.aead.AESGCM.encrypt returns ciphertext + tag.
    """
    aesgcm = AESGCM(master_key)
    nonce = os.urandom(NONCE_LENGTH)
    # encrypt(nonce, data, associated_data)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return ciphertext, nonce

def decrypt_password(ciphertext_with_tag: bytes, nonce: bytes, master_key: bytes) -> str:
    """
    Decrypts data using AES-256-GCM.
    """
    aesgcm = AESGCM(master_key)
    try:
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
        return plaintext_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError("Decryption failed. Invalid Key or Data Corrupted.") from e

def hash_master_password(password: str) -> str:
    """Hashes the master password for storage (authentication)."""
    return ph.hash(password)

def verify_master_password(password: str, hash_str: str) -> bool:
    """Verifies the master password against the stored hash."""
    try:
        return ph.verify(hash_str, password)
    except VerifyMismatchError:
        return False
