import os
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from dotenv import load_dotenv

from app.db.database import get_db
from app.crud import crud_chat
from fastapi import HTTPException

load_dotenv()
router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

class ConnectionManager:
    def __init__(self):
        # Lưu mọi người đang chat hệ thống
        self.global_users: list[WebSocket] = []
        # Lưu người đang online để chat riêng {user_id: websocket}
        self.private_users: dict[int, WebSocket] = {}

    async def connect_global(self, websocket: WebSocket):
        await websocket.accept()
        self.global_users.append(websocket)

    def disconnect_global(self, websocket: WebSocket):
        if websocket in self.global_users:
            self.global_users.remove(websocket)

    async def broadcast_global(self, message: dict):
        for connection in self.global_users:
            await connection.send_json(message)

    async def connect_private(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.private_users[user_id] = websocket

    def disconnect_private(self, user_id: int):
        if user_id in self.private_users:
            del self.private_users[user_id]

    async def send_private(self, message: dict, receiver_id: int):
        if receiver_id in self.private_users:
            await self.private_users[receiver_id].send_json(message)

manager = ConnectionManager()

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except:
        raise ValueError("Invalid Token")

# --- 1. LUỒNG CHAT HỆ THỐNG ---
@router.websocket("/ws/global")
async def global_chat(websocket: WebSocket, token: str = Query(...), sender_name: str = Query("User"), db: Session = Depends(get_db)):
    try:
        user_id = verify_token(token)
    except:
        await websocket.close(code=1008)
        return

    await manager.connect_global(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = crud_chat.create_message(db, user_id, sender_name, data)
            
            # ĐẢM BẢO KEY LÀ sender_name VÀ sender_id
            await manager.broadcast_global({
                "type": "global", 
                "sender_id": user_id,
                "sender_name": sender_name, 
                "message": data, 
                "time": msg.created_at.isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect_global(websocket)

# --- 2. LUỒNG CHAT RIÊNG (1-1) ---
@router.websocket("/ws/private")
async def private_chat(websocket: WebSocket, token: str = Query(...), sender_name: str = Query("User"), db: Session = Depends(get_db)):
    try:
        user_id = verify_token(token)
    except:
        await websocket.close(code=1008)
        return

    await manager.connect_private(websocket, user_id)
    try:
        while True:
            raw_data = await websocket.receive_text()
            payload = json.loads(raw_data)
            receiver_id = payload.get("receiver_id")
            message = payload.get("message")

            msg = crud_chat.create_message(db, user_id, sender_name, message, receiver_id)
            chat_data = {
                "type": "private", 
                "sender_id": user_id, # Thêm cái này
                "sender_name": sender_name, 
                "message": message
            }
            await manager.send_private(chat_data, receiver_id)
            await websocket.send_json(chat_data)
    except WebSocketDisconnect:
        manager.disconnect_private(user_id)

# ==========================================
# API TẢI LỊCH SỬ CHAT (Thêm vào cuối file)
# ==========================================
@router.get("/history/global")
def get_global_chat_history(db: Session = Depends(get_db)):
    messages = crud_chat.get_global_history(db, limit=50) # Lấy 50 tin nhắn gần nhất
    # Format lại để Frontend dễ đọc
    return [{"id": m.id, "sender_id": m.user_id, "sender_name": m.sender_name, "message": m.message, "time": m.created_at} for m in messages]

@router.get("/history/private/{receiver_id}")
def get_private_chat_history(receiver_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    try:
        user_id = verify_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Token")
        
    messages = crud_chat.get_private_history(db, user1_id=user_id, user2_id=receiver_id, limit=50)
    return [{"id": m.id, "sender_id": m.user_id, "sender_name": m.sender_name, "message": m.message, "time": m.created_at} for m in messages]