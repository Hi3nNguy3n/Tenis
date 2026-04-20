import os
import json
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from dotenv import load_dotenv
from datetime import datetime, timezone

from app.db.database import get_db
from app.crud import crud_chat
from fastapi import HTTPException

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
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
            try:
                await self.private_users[receiver_id].send_json(message)
                print(f"WS: Message sent to user {receiver_id}")
            except Exception as e:
                print(f"WS Error sending to {receiver_id}: {e}")
                del self.private_users[receiver_id]
        else:
            print(f"WS: Receiver {receiver_id} is not connected. Current online: {list(self.private_users.keys())}")

manager = ConnectionManager()

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except:
        raise ValueError("Invalid Token")

def format_datetime(dt):
    if not dt: return None
    # Đảm bảo có thông tin timezone để Frontend không bị lệch 7 tiếng
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

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
            
            await manager.broadcast_global({
                "type": "global", 
                "sender_id": user_id,
                "sender_name": sender_name, 
                "message": data, 
                "time": format_datetime(msg.created_at)
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

            try:
                if payload.get("type") == "typing":
                    receiver_id = int(payload.get("receiver_id"))
                    if receiver_id:
                        await manager.send_private({
                            "type": "typing",
                            "sender_id": user_id,
                            "receiver_id": receiver_id,
                            "sender_name": sender_name,
                            "is_typing": bool(payload.get("is_typing", True)),
                        }, receiver_id)
                        await websocket.send_json({
                            "type": "typing",
                            "sender_id": user_id,
                            "receiver_id": receiver_id,
                            "sender_name": sender_name,
                            "is_typing": bool(payload.get("is_typing", True)),
                        })
                    continue

                receiver_id = int(payload.get("receiver_id"))
                message = payload.get("message")
                
                if not message or not receiver_id:
                    continue

                msg = crud_chat.create_message(db, user_id, sender_name, message, receiver_id)
                print(f"DEBUG: Saved message from {user_id} to {receiver_id}: {message[:20]}...")
                
                chat_data = {
                    "type": "private", 
                    "sender_id": user_id,
                    "sender_name": sender_name, 
                    "message": message,
                    "receiver_id": receiver_id,
                    "time": format_datetime(msg.created_at)
                }
                await manager.send_private(chat_data, receiver_id)
                await websocket.send_json(chat_data)
            except (ValueError, TypeError) as e:
                print(f"DEBUG Error processing private msg: {e}")
                continue
    except WebSocketDisconnect:
        manager.disconnect_private(user_id)

@router.get("/history/global")
def get_global_chat_history(db: Session = Depends(get_db)):
    messages = crud_chat.get_global_history(db, limit=50)
    return [{"id": m.id, "sender_id": m.user_id, "sender_name": m.sender_name, "message": m.message, "time": format_datetime(m.created_at)} for m in messages]

@router.get("/history/private/{receiver_id}")
def get_private_chat_history(receiver_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    try:
        user_id = verify_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Token")
        
    messages = crud_chat.get_private_history(db, user1_id=user_id, user2_id=receiver_id, limit=50)
    return [{"id": m.id, "sender_id": m.user_id, "sender_name": m.sender_name, "message": m.message, "time": format_datetime(m.created_at)} for m in messages]

@router.get("/threads/private")
def get_private_threads(token: str = Query(...), db: Session = Depends(get_db)):
    try:
        user_id = verify_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
    threads = crud_chat.get_private_thread_summaries(db, user_id=user_id)
    for t in threads:
        if isinstance(t.get('updatedAt'), datetime):
             t['updatedAt'] = format_datetime(t['updatedAt'])
    return threads

@router.put("/mark-read/{other_user_id}")
def mark_as_read(other_user_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    try:
        user_id = verify_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
    count = crud_chat.mark_private_messages_as_read(db, reader_id=user_id, other_user_id=other_user_id)
    return {"status": "ok", "marked_count": count}

@router.delete("/thread/{other_user_id}")
def delete_thread(other_user_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    try:
        user_id = verify_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
    deleted_count = crud_chat.delete_private_thread(db, user1_id=user_id, user2_id=other_user_id)
    return {"status": "ok", "deleted_count": deleted_count}
