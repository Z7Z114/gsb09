from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
import json

router = APIRouter(prefix="/messages", tags=["messages"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        # 重复摘除不得抛异常
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # 对单个坏连接免疫：摘除发送失败的连接，继续广播给其余连接
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
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

    db_message = models.Message(**message.dict())
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
            except (json.JSONDecodeError, TypeError):
                # 非法 JSON：告知客户端后继续存活，连接不得崩溃或残留
                await websocket.send_json({"error": "非法的消息格式：需要 JSON 对象"})
                continue

            if not isinstance(message_data, dict):
                await websocket.send_json({"error": "非法的消息格式：需要 JSON 对象"})
                continue

            content = str(message_data.get("content") or "").strip()
            if not content:
                await websocket.send_json({"error": "消息内容不能为空"})
                continue

            from ..database import SessionLocal
            db = SessionLocal()
            try:
                craftsman_id = message_data.get("craftsman_id")
                if craftsman_id is not None:
                    craftsman = db.query(models.Craftsman).filter(
                        models.Craftsman.id == craftsman_id
                    ).first()
                    if not craftsman:
                        await websocket.send_json({"error": "匠人不存在"})
                        continue

                db_message = models.Message(
                    content=content,
                    craftsman_id=craftsman_id,
                    message_type=message_data.get("message_type", "chat")
                )
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
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        # 异常断开也必须从 active_connections 中摘除，避免连接泄漏
        manager.disconnect(websocket)
