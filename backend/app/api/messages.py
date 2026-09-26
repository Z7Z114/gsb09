from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db, SessionLocal
import json

router = APIRouter(prefix="/messages", tags=["messages"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        # 重复摘除不应抛异常
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # 单个坏连接不得中断广播：摘除它并继续发给其余连接
        stale = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection)


manager = ConnectionManager()


@router.get("/", response_model=List[schemas.Message])
def list_messages(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200),
                  db: Session = Depends(get_db)):
    messages = db.query(models.Message).order_by(models.Message.timestamp.desc()).offset(skip).limit(limit).all()
    return messages


@router.get("/{message_id}", response_model=schemas.Message)
def get_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.post("/", response_model=schemas.Message)
async def create_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    if message.craftsman_id is not None:
        craftsman = db.query(models.Craftsman).filter(
            models.Craftsman.id == message.craftsman_id
        ).first()
        if not craftsman:
            raise HTTPException(status_code=404, detail="Craftsman not found")

    db_message = models.Message(**message.model_dump())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    db_message = db.query(models.Message).filter(models.Message.id == db_message.id).first()
    
    message_data = {
        "id": db_message.id,
        "content": db_message.content,
        "craftsman_id": db_message.craftsman_id,
        "timestamp": db_message.timestamp.isoformat(),
        "message_type": db_message.message_type,
        "craftsman": {
            "id": db_message.craftsman.id,
            "name": db_message.craftsman.name,
            "school": db_message.craftsman.school
        } if db_message.craftsman else None
    }
    
    await manager.broadcast(message_data)
    
    return db_message


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                if not isinstance(message_data, dict):
                    raise ValueError("消息必须是 JSON 对象")
                message = schemas.MessageCreate(**message_data)
            except (json.JSONDecodeError, ValueError) as exc:
                # 非法输入：回错误提示并保持连接存活，不得让连接变僵尸
                await websocket.send_json({"type": "error", "detail": f"非法消息：{exc}"})
                continue

            db = SessionLocal()
            try:
                if message.craftsman_id is not None:
                    craftsman = db.query(models.Craftsman).filter(
                        models.Craftsman.id == message.craftsman_id
                    ).first()
                    if not craftsman:
                        await websocket.send_json({"type": "error", "detail": "匠人不存在"})
                        continue

                db_message = models.Message(**message.model_dump())
                db.add(db_message)
                db.commit()
                db.refresh(db_message)
                
                db_message = db.query(models.Message).filter(models.Message.id == db_message.id).first()
                
                response = {
                    "id": db_message.id,
                    "content": db_message.content,
                    "craftsman_id": db_message.craftsman_id,
                    "timestamp": db_message.timestamp.isoformat(),
                    "message_type": db_message.message_type,
                    "craftsman": {
                        "id": db_message.craftsman.id,
                        "name": db_message.craftsman.name,
                        "school": db_message.craftsman.school
                    } if db_message.craftsman else None
                }
                
                await manager.broadcast(response)
            finally:
                db.close()
    finally:
        # 正常断开或异常退出都必须安全摘除，避免连接泄漏
        manager.disconnect(websocket)
