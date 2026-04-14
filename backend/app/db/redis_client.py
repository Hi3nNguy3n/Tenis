# backend/app/db/redis_client.py
import redis
from app.core.config import settings

def get_redis():
    r = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True # Rất quan trọng để nhận về string thay vì bytes
    )
    try:
        yield r
    finally:
        r.close()