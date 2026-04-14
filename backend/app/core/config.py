# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://admin:secret@localhost:5432/saigon_tennis_db"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY" # Tương lai cũng nên đưa biến này vào .env
    ALGORITHM: str = "HS256"
    
    # Mail Config (Chỉ khai báo kiểu dữ liệu, không điền giá trị)
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    
    # Cloudinary (Chỉ khai báo kiểu dữ liệu)
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()