import sqlalchemy
from sqlalchemy import text

DATABASE_URL = 'postgresql://admin:secret@localhost:5433/tennis_chat_db'
engine = sqlalchemy.create_engine(DATABASE_URL)

def migrate():
    print(f"Connecting to {DATABASE_URL}...")
    with engine.connect() as conn:
        print("Checking/Adding missing columns...")
        # Add is_read
        try:
            conn.execute(text("ALTER TABLE chat_messages ADD COLUMN is_read BOOLEAN DEFAULT FALSE"))
            print("Added is_read column.")
        except Exception as e:
            print(f"Skipping is_read: {e}")
            
        # Add read_at
        try:
            conn.execute(text("ALTER TABLE chat_messages ADD COLUMN read_at TIMESTAMP"))
            print("Added read_at column.")
        except Exception as e:
            print(f"Skipping read_at: {e}")
        
        conn.commit()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
