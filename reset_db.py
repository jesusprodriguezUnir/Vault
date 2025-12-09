from app.database import engine, Base
from app import models

def reset_db():
    print("WARNING: This will delete ALL data in the database.")
    # confirm = input("Type 'yes' to confirm: ")
    # if confirm != "yes":
    #     print("Aborted.")
    #     return

    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Database cleared. Please refresh the web page to see the Setup screen.")

if __name__ == "__main__":
    reset_db()
