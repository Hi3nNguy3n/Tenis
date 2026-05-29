from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, players, tournaments, registrations, payments, courts, matches, logs, news, upload, challenges, marketing
from app.db.seed import seed_data
from app.core.config import settings
from app.core.cloudinary_setup import init_cloudinary
from app.core.tasks import start_scheduler
from app.core.middleware import SecurityHeadersMiddleware, SimpleRateLimitMiddleware
import logging

from app.db.database import engine
from app.models.models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Saigon Tennis Tour API")

@app.middleware("http")
async def forward_proto_middleware(request: Request, call_next):
    if request.headers.get("x-forwarded-proto") == "https":
        request.scope["scheme"] = "https"
    response = await call_next(request)
    return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    SimpleRateLimitMiddleware,
    requests_per_window=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    auth_requests_per_window=settings.RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL EXCEPTION HANDLERS ---
def _cors_error_headers(request: Request) -> dict:
    origin = request.headers.get("origin")
    if origin and origin in settings.frontend_origins:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    return {}


@app.exception_handler(OperationalError)
async def db_connection_exception_handler(request: Request, exc: OperationalError):
    logger.error(f"DATABASE CONNECTION LOST: {exc}")
    return JSONResponse(
        status_code=503,
        content={
            "detail": "DATABASE_ERROR", 
            "message": "Không thể kết nối đến máy chủ cơ sở dữ liệu. Vui lòng kiểm tra lại cấu hình kết nối."
        },
        headers=_cors_error_headers(request)
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("GLOBAL ERROR")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "INTERNAL_SERVER_ERROR",
            "message": "Đã xảy ra lỗi hệ thống. Vui lòng liên hệ quản trị viên."
        },
        headers=_cors_error_headers(request)
    )

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*50)
    print("[INIT] Dang khoi tao ket noi Cloudinary...")
    init_cloudinary()
    
    # THÊM ĐOẠN NÀY ĐỂ TỰ ĐỘNG TẠO BẢNG
    print("[INIT] Dang dong bo cau truc Database...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[SUCCESS] Tao cau truc bang thanh cong!")
    except Exception as e:
        print(f"[ERROR] Loi tao bang: {e}")
    # ----------------------------------------
    
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
app.include_router(marketing.router, prefix="/api/marketing", tags=["Marketing"])

@app.get("/")
def root():
    return {"message": "Welcome to Saigon Tennis Tour API"}
