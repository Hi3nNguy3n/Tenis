from app.db.database import engine
from sqlalchemy import text

def add_missing_columns():
    with engine.connect() as conn:
        print("Checking and adding missing columns to matches and match_challenges tables...")
        try:
            # Table matches
            conn.execute(text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS player_a2_id INTEGER REFERENCES players(id)"))
            print("Added player_a2_id column to matches.")
            
            conn.execute(text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS player_b2_id INTEGER REFERENCES players(id)"))
            print("Added player_b2_id column to matches.")
            
            conn.execute(text("ALTER TABLE matches ADD COLUMN IF NOT EXISTS match_type VARCHAR(30) DEFAULT 'singles'"))
            print("Added match_type column to matches.")
            
            # Table match_challenges
            conn.execute(text("ALTER TABLE match_challenges ADD COLUMN IF NOT EXISTS challenger_partner_id BIGINT REFERENCES players(id)"))
            print("Added challenger_partner_id column to match_challenges.")
            
            conn.execute(text("ALTER TABLE match_challenges ADD COLUMN IF NOT EXISTS challenged_partner_id BIGINT REFERENCES players(id)"))
            print("Added challenged_partner_id column to match_challenges.")
            
            conn.execute(text("ALTER TABLE match_challenges ADD COLUMN IF NOT EXISTS match_type VARCHAR(30) DEFAULT 'singles'"))
            print("Added match_type column to match_challenges.")
            
            conn.commit()
            print("Successfully updated database schema with doubles columns.")
        except Exception as e:
            print(f"Error updating database: {e}")

if __name__ == "__main__":
    add_missing_columns()
