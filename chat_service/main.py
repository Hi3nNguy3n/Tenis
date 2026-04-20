from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat
from app.db.database import engine, Base

# Tự động tạo bảng khi chạy server
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Saigon Tennis - Chat Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép Frontend Vue kết nối
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

# Chạy lệnh này ở terminal: uvicorn main:app --reload --port 8001
