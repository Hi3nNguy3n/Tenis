from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Cấu hình Database
    DATABASE_URL: str
    
    # Cấu hình Frontend & Redis (Có thể để mặc định vì không nhạy cảm)
    FRONTEND_ORIGINS: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "http://localhost:4173,"
        "http://127.0.0.1:4173"
    )
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    BREVO_API_KEY: str = ""
    # Auth - BẮT BUỘC (Chỉ khai báo kiểu chữ, không gán mặc định)
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"

    # Mail Config - Thông tin nhạy cảm bỏ mặc định
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"

    # Cloudinary - Thông tin nhạy cảm bỏ mặc định
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )

    @property
    def frontend_origins(self) -> list[str]:
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]

settings = Settings()