from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, players, tournaments, registrations, payments, courts, matches, logs, news, upload, challenges
from app.db.seed import seed_data
from app.core.config import settings
from app.core.cloudinary_setup import init_cloudinary
from app.core.tasks import start_scheduler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Saigon Tennis Tour API")

# --- CORS SETTINGS ---
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "https://saigon-tennis-frontend-deploy.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL EXCEPTION HANDLERS ---
@app.exception_handler(OperationalError)
async def db_connection_exception_handler(request: Request, exc: OperationalError):
    logger.error(f"DATABASE CONNECTION LOST: {exc}")
    # Đảm bảo trả về header CORS ngay cả khi có lỗi DB
    return JSONResponse(
        status_code=503,
        content={
            "detail": "DATABASE_ERROR", 
            "message": "Không thể kết nối đến máy chủ cơ sở dữ liệu. Vui lòng kiểm tra lại cấu hình kết nối (IPWhitelist, pg_hba.conf, firewall)."
        },
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true"
        }
    )

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*50)
    print("[INIT] Dang khoi tao ket noi Cloudinary...")
    init_cloudinary()
    
    print("[INIT] Dang kiem tra va khoi tao du lieu mau (Seed Data)...")
    try:
        seed_data()
    except OperationalError as e:
        print(f"[WARNING] Khong the chay Seed Data vi loi ket noi Database: {e}")
    except Exception as e:
        print(f"[ERROR] Loi khong xac dinh khi chay Seed Data: {e}")

    print("[INIT] Dang khoi dong trinh don dep tu dong (Scheduler)...")
    start_scheduler()
    
    print("[SUCCESS] API Server da san sang phuc vu!")
    print("="*50 + "\n")

# --- ROUTERS ---
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(players.router, prefix="/api/players", tags=["Players"])
app.include_router(tournaments.router, prefix="/api/tournaments", tags=["Tournaments"])
app.include_router(registrations.router, prefix="/api/registrations", tags=["Registrations"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(courts.router, prefix="/api/courts", tags=["Courts"])
app.include_router(matches.router, prefix="/api/matches", tags=["Matches"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload System"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["Challenges"])

@app.get("/")
def root():
    return {"message": "Welcome to Saigon Tennis Tour API"}
