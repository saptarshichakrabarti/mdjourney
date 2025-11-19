import sqlite3
import os

DB_FILE = "auth/data/mdjourney.db"
SCHEMA_FILE = "auth/migrations/001_init.sql"

def initialize_database():
    """Initializes the SQLite database, creating the schema and performing checks."""
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

    # Connect to the database (it will be created if it doesn't exist)
    print(f"Connecting to database at {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Apply the schema
        print(f"Applying schema from {SCHEMA_FILE}...")
        with open(SCHEMA_FILE, 'r') as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
        print("Schema applied successfully.")

        # Confirm WAL mode and synchronous settings
        print("Setting WAL mode...")
        cursor.execute("PRAGMA journal_mode=WAL;")
        journal_mode = cursor.fetchone()
        print(f"Journal mode is: {journal_mode[0]}")

        print("Setting synchronous mode to FULL...")
        cursor.execute("PRAGMA synchronous=FULL;")
        sync_mode = cursor.fetchone()


        # Perform an integrity check
        print("Running database integrity check...")
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()
        print(f"Integrity check result: {integrity_result[0]}")

        if integrity_result[0] != 'ok':
            raise Exception("Database integrity check failed!")

        conn.commit()
        print("Database initialized successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    initialize_database()
