# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, players, tournaments, registrations, payments, courts, matches, logs, news, upload, challenges
from app.db.seed import seed_data
from app.core.config import settings
from app.core.cloudinary_setup import init_cloudinary
from app.core.tasks import start_scheduler

app = FastAPI(title="Saigon Tennis Tour API")

origins = [
    "http://localhost:5173",         # Cho phép lúc dev local
    "http://localhost:3000",
    "https://saigon-tennis-frontend-deploy.vercel.app", # LINK VERCEL CỦA ÔNG
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*50)
    print("[INIT] Dang khoi tao ket noi Cloudinary...")
    init_cloudinary()
    print("[INIT] Dang kiem tra va khoi tao du lieu mau (Seed Data)...")
    seed_data()
    print("[INIT] Dang khoi dong trinh don dep tu dong (Scheduler)...")
    start_scheduler()
    print("[SUCCESS] API Server da san sang phuc vu!")
    print("="*50 + "\n")

# Nhúng các router vào app
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(players.router, prefix="/api/players", tags=["Players"])
app.include_router(tournaments.router, prefix="/api/tournaments", tags=["Tournaments"])
app.include_router(registrations.router, prefix="/api/registrations", tags=["Registrations"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(courts.router, prefix="/api/courts", tags=["Courts"])
app.include_router(matches.router, prefix="/api/matches", tags=["Matches"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload System"]) # 2. Khai báo
app.include_router(challenges.router, prefix="/api/challenges", tags=["Challenges"])

@app.get("/")
def root():
    return {"message": "Welcome to Saigon Tennis Tour API"}
