from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://admin:secret@localhost:5432/saigon_tennis_db"
    FRONTEND_ORIGINS: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "http://localhost:4173,"
        "http://127.0.0.1:4173"
    )
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY"
    ALGORITHM: str = "HS256"

    # Mail Config (Defaults provided for development)
    MAIL_USERNAME: str = "minhphu25102005@gmail.com"
    MAIL_PASSWORD: str = "gfnt djph anuf vdxi"
    MAIL_FROM: str = "minhphu25102005@gmail.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"

    # Cloudinary (Defaults provided for development)
    CLOUDINARY_CLOUD_NAME: str = "dfs9o3bny"
    CLOUDINARY_API_KEY: str = "513954498387371"
    CLOUDINARY_API_SECRET: str = "Brss7LepXirwlYHuPWMfnsLguko"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )

    @property
    def frontend_origins(self) -> list[str]:
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]


settings = Settings()
