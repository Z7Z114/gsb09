from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from .. import models, schemas
from ..database import get_db
from ..services.archive_service import archive_service
from ..services.email_service import email_service
from datetime import datetime
import json

router = APIRouter(prefix="/archives", tags=["archives"])


@router.get("/", response_model=List[schemas.CraftArchive])
def list_archives(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200),
                  db: Session = Depends(get_db)):
    archives = db.query(models.CraftArchive).order_by(models.CraftArchive.generated_at.desc()).offset(skip).limit(limit).all()
    return archives


@router.get("/{archive_id}", response_model=schemas.CraftArchive)
def get_archive(archive_id: int, db: Session = Depends(get_db)):
    archive = db.query(models.CraftArchive).filter(models.CraftArchive.id == archive_id).first()
    if not archive:
        raise HTTPException(status_code=404, detail="Archive not found")
    return archive


@router.post("/generate/{recording_id}")
def generate_archive(recording_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    recording = db.query(models.AudioRecording).filter(models.AudioRecording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    if recording.status != "transcribed":
        raise HTTPException(status_code=400, detail="Recording not fully transcribed yet")
    
    transcripts = db.query(models.Transcript).filter(models.Transcript.recording_id == recording_id).all()
    diarizations = db.query(models.SpeakerDiarization).filter(models.SpeakerDiarization.recording_id == recording_id).all()
    
    transcript_dicts = []
    for t in transcripts:
        speaker_info = next((d for d in diarizations 
                           if abs(d.start_time - t.start_time) < 0.5), None)
        transcript_dicts.append({
            "content": t.content,
            "start_time": t.start_time,
            "end_time": t.end_time,
            "speaker_label": speaker_info.speaker_label if speaker_info else "UNKNOWN",
            "predicted_school": speaker_info.predicted_school if speaker_info else "未知流派"
        })
    
    craftsmen = db.query(models.Craftsman).all()
    craftsman_dicts = [{"id": c.id, "name": c.name, "school": c.school} for c in craftsmen]
    
    audio_metadata = {
        "filename": recording.filename,
        "duration": recording.duration,
        "workshop": recording.workshop,
        "ambience_profile": {}
    }
    
    background_tasks.add_task(generate_archive_task, recording_id, transcript_dicts, craftsman_dicts, audio_metadata, db)
    
    return {
        "status": "generating",
        "message": "Archive generation started in background",
        "recording_id": recording_id
    }


def generate_archive_task(recording_id: int, transcripts: List[Dict[str, Any]], 
                           craftsmen: List[Dict[str, Any]], audio_metadata: Dict[str, Any], db: Session):
    try:
        archive_data = archive_service.generate_archive_summary(transcripts, craftsmen, audio_metadata)

        transcript_ids = db.query(models.Transcript.id).filter(
            models.Transcript.recording_id == recording_id
        ).all()
        transcript_id_list = [t[0] for t in transcript_ids]

        # 离线摘要的可识别标记随档案一起落库，不得伪装成真实摘要
        content = archive_data.get("content", {}) or {}
        if archive_data.get("is_fallback"):
            content = {**content, "is_fallback": True}

        db_archive = models.CraftArchive(
            title=archive_data.get("title", "传统弓箭制作工艺档案"),
            summary=archive_data.get("summary", ""),
            content=content,
            keywords=archive_data.get("keywords", []),
            related_transcript_ids=transcript_id_list
        )
        db.add(db_archive)
        db.commit()
        db.refresh(db_archive)
        
    except Exception as e:
        print(f"Error generating archive for recording {recording_id}: {e}")


@router.get("/{archive_id}/html")
def get_archive_html(archive_id: int, db: Session = Depends(get_db)):
    archive = db.query(models.CraftArchive).filter(models.CraftArchive.id == archive_id).first()
    if not archive:
        raise HTTPException(status_code=404, detail="Archive not found")
    
    archive_data = {
        "title": archive.title,
        "summary": archive.summary,
        "key_points": archive.content.get("key_points", []) if archive.content else [],
        "school_analysis": archive.content.get("school_analysis", {}) if archive.content else {},
        "heritage_value": archive.content.get("heritage_value", "待评估") if archive.content else "待评估",
        "keywords": archive.keywords or []
    }
    
    html_content = archive_service.generate_html_archive(archive_data)
    
    return {
        "archive_id": archive_id,
        "html_content": html_content
    }


@router.post("/send-email")
async def send_archive_email(request: schemas.ArchiveEmailRequest, db: Session = Depends(get_db)):
    archive = db.query(models.CraftArchive).filter(models.CraftArchive.id == request.archive_id).first()
    if not archive:
        raise HTTPException(status_code=404, detail="Archive not found")
    
    archive_data = {
        "title": archive.title,
        "summary": archive.summary,
        "key_points": archive.content.get("key_points", []) if archive.content else [],
        "school_analysis": archive.content.get("school_analysis", {}) if archive.content else {},
        "heritage_value": archive.content.get("heritage_value", "待评估") if archive.content else "待评估",
        "keywords": archive.keywords or []
    }
    
    html_content = archive_service.generate_html_archive(archive_data)
    
    result = await email_service.send_archive_email(
        archive_data,
        html_content,
        request.recipient_email,
        request.custom_message
    )
    
    # 只有确实投递成功才标记已发送；未配置或投递失败时保持原状
    if result.get("success"):
        archive.sent_to_feiyi = 1
        archive.sent_at = datetime.utcnow()
        db.commit()

    return result
