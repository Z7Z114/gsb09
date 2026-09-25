from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/craftsmen", tags=["craftsmen"])


@router.get("/", response_model=List[schemas.Craftsman])
def list_craftsmen(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    craftsmen = db.query(models.Craftsman).offset(skip).limit(limit).all()
    return craftsmen


@router.get("/{craftsman_id}", response_model=schemas.Craftsman)
def get_craftsman(craftsman_id: int, db: Session = Depends(get_db)):
    craftsman = db.query(models.Craftsman).filter(models.Craftsman.id == craftsman_id).first()
    if not craftsman:
        raise HTTPException(status_code=404, detail="Craftsman not found")
    return craftsman


@router.post("/", response_model=schemas.Craftsman)
def create_craftsman(craftsman: schemas.CraftsmanCreate, db: Session = Depends(get_db)):
    db_craftsman = models.Craftsman(**craftsman.dict())
    db.add(db_craftsman)
    db.commit()
    db.refresh(db_craftsman)
    return db_craftsman


@router.put("/{craftsman_id}", response_model=schemas.Craftsman)
def update_craftsman(craftsman_id: int, craftsman: schemas.CraftsmanCreate, db: Session = Depends(get_db)):
    db_craftsman = db.query(models.Craftsman).filter(models.Craftsman.id == craftsman_id).first()
    if not db_craftsman:
        raise HTTPException(status_code=404, detail="Craftsman not found")
    
    for key, value in craftsman.dict().items():
        setattr(db_craftsman, key, value)
    
    db.commit()
    db.refresh(db_craftsman)
    return db_craftsman


@router.delete("/{craftsman_id}")
def delete_craftsman(craftsman_id: int, db: Session = Depends(get_db)):
    db_craftsman = db.query(models.Craftsman).filter(models.Craftsman.id == craftsman_id).first()
    if not db_craftsman:
        raise HTTPException(status_code=404, detail="Craftsman not found")
    
    db.delete(db_craftsman)
    db.commit()
    return {"message": "Craftsman deleted successfully"}
