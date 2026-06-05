import asyncio
import logging
from app.db.database import SessionLocal
from app.crud import crud_chat

# Set up logging
logger = logging.getLogger("chat_service.tasks")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

async def clean_old_messages_task():
    """
    Background loop that runs every 24 hours to delete messages older than 15 days from the database.
    """
    # Wait a bit on startup to let the server initialize fully
    await asyncio.sleep(10)
    
    while True:
        try:
            logger.info("Starting scheduled chat messages cleanup (older than 15 days)...")
            db = SessionLocal()
            try:
                deleted_count = crud_chat.delete_old_messages(db, days=15)
                logger.info(f"Cleanup finished. Successfully deleted {deleted_count} old messages.")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error occurred during chat messages cleanup: {str(e)}")
        
        # Run once every 24 hours (86400 seconds)
        await asyncio.sleep(86400)

def start_cleanup_task():
    """
    Launches the clean_old_messages_task in the background event loop.
    """
    logger.info("Initializing background chat messages cleanup task...")
    asyncio.create_task(clean_old_messages_task())
