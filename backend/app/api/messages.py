from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
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
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


@router.get("/", response_model=List[schemas.Message])
def list_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
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
            message_data = json.loads(data)
            
            from fastapi import Depends
            from ..database import SessionLocal
            db = SessionLocal()
            try:
                db_message = models.Message(
                    content=message_data.get("content", ""),
                    craftsman_id=message_data.get("craftsman_id"),
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
