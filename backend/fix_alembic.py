import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    conn.execute(text("UPDATE alembic_version SET version_num = '0d92b4cb3a7a'"))
    conn.commit()
print("Done")
