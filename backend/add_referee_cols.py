from app.db.database import engine
from sqlalchemy import text

def add_missing_columns():
    with engine.connect() as conn:
        print("Checking and adding missing columns to matches table...")
        try:
            # Check for referee_name
            conn.execute(text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS referee_name VARCHAR(255)"))
            print("Added referee_name column if it didn't exist.")
            
            # Check for referee_phone
            conn.execute(text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS referee_phone VARCHAR(50)"))
            print("Added referee_phone column if it didn't exist.")
            
            conn.commit()
            print("Successfully updated database schema.")
        except Exception as e:
            print(f"Error updating database: {e}")

if __name__ == "__main__":
    add_missing_columns()
