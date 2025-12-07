# 🔐 Secure Password Vault

A self-hosted, Dockerized Password Manager with AES-256 encryption.

## Architecture
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL (Dockerized)
- **Security**: 
  - **Cipher**: AES-256-GCM (Authenticated Encryption)
  - **Key Derivation**: Argon2id (Master Password -> Encryption Key)
  - **Auth**: Argon2id Hash of Master Password
- **Frontend**: Simple HTML/JS (Single Page Application)

## Prerequisites
- Docker Engine
- Docker Compose

## Quick Start 🚀

1.  **Build and Run**:
    ```powershell
    docker-compose up --build
    ```
    *Wait for the logs to say `Uvicorn running on http://0.0.0.0:8000` and `Database connection successful`.*

2.  **Access the Vault**:
    Open your browser to: [http://localhost:8001](http://localhost:8001)

3.  **Usage**:
    1.  **Initialize**: Enter a Username and a **Master Password**.
## Running Locally (Hybrid Mode) 🛠️
*Recommended for development. Uses Docker for DB, but runs Python locally.*

1.  **Start Database**:
    ```powershell
    docker-compose up -d db
    ```

2.  **Install Dependencies**:
    ```powershell
    pip install -r requirements.txt
    pip install psycopg2-binary
    ```

3.  **Run Application**:
    ```powershell
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    Access at: [http://localhost:8000](http://localhost:8000)

## Clean Up
To stop the application:
```powershell
docker-compose down
```
To delete data (reset everything):
```powershell
docker-compose down -v
```
