from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat
from app.db.database import engine, Base
from app.core.middleware import SecurityHeadersMiddleware, SimpleRateLimitMiddleware
import os

# Tự động tạo bảng khi chạy server
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Saigon Tennis - Chat Microservice")

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    SimpleRateLimitMiddleware,
    requests_per_window=int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "120")),
)

origins = [
    "http://localhost:5173",
    "https://saigon-tennis-frontend-deploy.vercel.app", # Link Vercel của 
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

# Chạy lệnh này ở terminal: uvicorn main:app --reload --port 8001
