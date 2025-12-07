# Secure Password Vault v2.0

A self-hosted, simplified password manager designed for security and portability. 
Built with **FastAPI**, **PostgreSQL/SQLite**, and **Docker**.

## Features 🚀

- **Hierarchical Storage**: Organize passwords by `Category` -> `Application` -> `Password Entries`.
- **Encryption**: AES-256-GCM encryption for all sensitive fields. Keys are derived from your Master Password using Argon2id.
- **Zero-Knowledge Architecture**: The detailed master password is never stored on disk.
- **Modern UI**: Single Page Application (SPA) with Sidebar navigation, Search, and Filters.
- **Bulk Operations**:
  - Import/Export standard JSON format.
  - Large-scale Seeding Scripts included.
- **Full CRUD**: Create, Read, Update, Delete for Categories, Applications, and Passwords.

## Architecture 🏗️

### Backend (`app/`)
- **FastAPI**: High-performance API.
- **SQLAlchemy**: ORM for database interactions.
- **Security**: strict `verify_master_password` check on all write operations.
- **Database**: 
    - `categories`: High-level groups (Work, Personal).
    - `applications`: specific services (Jira, Gmail).
    - `passwords`: actual credentials (encrypted).

### Frontend (`static/`)
- Vanilla JS/HTML5 SPA.
- Responsive Sidebar layout.
- interactive Modals for management.

## Installation & Running 🛠️

Prerequisites: **Docker** and **Docker Compose**.

1. **Clone/Open the project**.
2. **Start the stack**:
   ```bash
   docker-compose up -d --build
   ```
3. **Access the Application**:
   Open **[http://localhost:8001](http://localhost:8001)** in your browser.

4. **Initial Setup**:
   The first time you load the page, you will be prompted to create a **Master Password**. MEmorize it! There is no recovery.

## Development Tools 🧪

### Test Suite
Run the automated tests (using `pytest`):
```bash
docker-compose exec web pytest tests/ -v
```

### Data Seeding
Populate the database with sample data (20 Categories, 100 Apps):
```bash
# 1. Clear existing DB (optional: docker-compose down -v)
# 2. Run Seed Script
docker-compose exec web python seed_data.py

# 3. Generate Passwords for all Apps
docker-compose exec web python seed_passwords.py
```

### Manual Verification
- **Import/Export**: Use the JSON buttons on the Dashboard.
- **Edit/Delete**: Use the action buttons in the Category/Application lists. Note that deleting a Category **cascades** and deletes all its applications.

## License
MIT
