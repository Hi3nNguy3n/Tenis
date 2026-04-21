import redis
import os
from app.core.config import settings

def get_redis():
    # Sử dụng link URL từ biến môi trường, nếu không có thì mặc định về localhost để dev
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    r = redis.from_url(
        redis_url,
        decode_responses=True # Giữ nguyên cái này để nhận về string
    )
    try:
        yield r
    finally:
        r.close()