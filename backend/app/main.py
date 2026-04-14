# backend/app/main.py
from fastapi import FastAPI
from app.api import auth, players, tournaments, registrations
from app.db.seed import seed_data  # <-- Bổ sung import hàm seed_data
from app.core.cloudinary_setup import init_cloudinary
from app.core.tasks import start_scheduler

app = FastAPI(title="Saigon Tennis Tour API")

# Định nghĩa sự kiện chạy 1 lần duy nhất khi khởi động Uvicorn
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*50)
    print("🔍 Đang khởi tạo kết nối Cloudinary...")
    init_cloudinary() # <-- BỔ SUNG DÒNG NÀY
    print("🔍 Đang kiểm tra và khởi tạo dữ liệu mẫu (Seed Data)...")
    seed_data()
    print("🔍 Đang khởi động trình dọn dẹp tự động (Scheduler)...")
    start_scheduler()
    print("✅ API Server đã sẵn sàng phục vụ!")
    print("="*50 + "\n")

# Nhúng các router vào app
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(players.router, prefix="/api/players", tags=["Players"])

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(players.router, prefix="/api/players", tags=["Players"])
app.include_router(tournaments.router, prefix="/api/tournaments", tags=["Tournaments"])

app.include_router(registrations.router, prefix="/api/registrations", tags=["Registrations"])

@app.get("/")
def root():
    return {"message": "Welcome to Saigon Tennis Tour API"}