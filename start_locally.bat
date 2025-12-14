@echo off
echo Starting Secure Password Vault Locally...
echo Setting up environment...

:: Use SQLite for local run
set DATABASE_URL=sqlite:///./vault.db

:: Install dependencies (Commented out as it causes issues, assuming env is ready)
:: echo Installing/Verifying dependencies...
:: pip install -r requirements.txt

:: Run the app
echo Starting Server at http://localhost:8000 ...
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
