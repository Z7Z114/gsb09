from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from .. import models, schemas
from ..database import get_db
from ..services.audio_service import audio_processor
from ..services.transcription_service import transcription_service
from ..services.diarization_service import diarization_service
import os
import uuid

router = APIRouter(prefix="/audio", tags=["audio"])

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg"}


@router.get("/recordings", response_model=List[schemas.AudioRecording])
def list_recordings(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200),
                    db: Session = Depends(get_db)):
    recordings = db.query(models.AudioRecording).order_by(models.AudioRecording.recorded_at.desc()).offset(skip).limit(limit).all()
    return recordings


@router.get("/recordings/{recording_id}", response_model=schemas.AudioRecording)
def get_recording(recording_id: int, db: Session = Depends(get_db)):
    recording = db.query(models.AudioRecording).filter(models.AudioRecording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return recording


@router.post("/upload")
async def upload_audio(file: UploadFile = File(...), workshop: str = "default", db: Session = Depends(get_db)):
    # 规整原始文件名：去掉任何路径成分（含 Windows 反斜杠），保留中文名
    safe_filename = os.path.basename((file.filename or "").replace("\\", "/"))
    if not safe_filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    file_extension = os.path.splitext(safe_filename)[1].lower()
    if file_extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 '{file_extension or '无扩展名'}'，仅允许："
                   f"{', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"
        )

    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    db_recording = models.AudioRecording(
        filename=safe_filename,
        original_path=file_path,
        workshop=workshop,
        status="uploaded"
    )
    db.add(db_recording)
    db.commit()
    db.refresh(db_recording)
    
    return {
        "recording_id": db_recording.id,
        "filename": safe_filename,
        "path": file_path,
        "status": "uploaded"
    }


@router.post("/process/{recording_id}", response_model=schemas.AudioProcessResponse)
def process_audio(recording_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    recording = db.query(models.AudioRecording).filter(models.AudioRecording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    recording.status = "processing"
    db.commit()
    
    background_tasks.add_task(process_audio_task, recording_id, db)
    
    return schemas.AudioProcessResponse(
        recording_id=recording_id,
        status="processing",
        message="Audio processing started in background"
    )


def process_audio_task(recording_id: int, db: Session):
    recording = db.query(models.AudioRecording).filter(models.AudioRecording.id == recording_id).first()
    if not recording:
        return
    
    try:
        processed_result = audio_processor.process_audio_for_transcription(
            recording.original_path,
            PROCESSED_DIR
        )
        
        recording.processed_path = processed_result["processed_path"]
        recording.duration = processed_result["duration"]
        recording.status = "processed"
        db.commit()
        
        transcription_result = transcription_service.transcribe_audio(processed_result["processed_path"])
        
        diarization_result = diarization_service.diarize_audio(processed_result["processed_path"])
        
        merged_segments = diarization_service.merge_diarization_and_transcript(
            diarization_result,
            transcription_result["segments"]
        )
        
        for segment in merged_segments:
            school_prediction = diarization_service.predict_school(
                segment["text"],
                segment["speaker_label"]
            )
            
            db_transcript = models.Transcript(
                recording_id=recording_id,
                content=segment["text"],
                start_time=segment["start_time"],
                end_time=segment["end_time"],
                language=transcription_result["language"]
            )
            db.add(db_transcript)
            
            db_diarization = models.SpeakerDiarization(
                recording_id=recording_id,
                speaker_label=segment["speaker_label"],
                start_time=segment["start_time"],
                end_time=segment["end_time"],
                predicted_school=school_prediction["predicted_school"],
                confidence=school_prediction["confidence"]
            )
            db.add(db_diarization)
        
        db.commit()
        
        recording.status = "transcribed"
        db.commit()
        
    except Exception as e:
        recording.status = "failed"
        db.commit()
        print(f"Error processing audio {recording_id}: {e}")


@router.get("/recordings/{recording_id}/transcripts", response_model=List[Dict[str, Any]])
def get_recording_transcripts(recording_id: int, db: Session = Depends(get_db)):
    recording = db.query(models.AudioRecording).filter(models.AudioRecording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    transcripts = db.query(models.Transcript).filter(models.Transcript.recording_id == recording_id).all()
    diarizations = db.query(models.SpeakerDiarization).filter(models.SpeakerDiarization.recording_id == recording_id).all()
    
    result = []
    for t in transcripts:
        speaker_info = next((d for d in diarizations 
                           if abs(d.start_time - t.start_time) < 0.5), None)
        
        result.append({
            "id": t.id,
            "content": t.content,
            "start_time": t.start_time,
            "end_time": t.end_time,
            "speaker_label": speaker_info.speaker_label if speaker_info else "UNKNOWN",
            "predicted_school": speaker_info.predicted_school if speaker_info else None,
            "confidence": speaker_info.confidence if speaker_info else None,
            "created_at": t.created_at
        })
    
    return result


@router.get("/recordings/{recording_id}/diarization", response_model=List[schemas.SpeakerDiarization])
def get_recording_diarization(recording_id: int, db: Session = Depends(get_db)):
    recording = db.query(models.AudioRecording).filter(models.AudioRecording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    diarizations = db.query(models.SpeakerDiarization).filter(
        models.SpeakerDiarization.recording_id == recording_id
    ).order_by(models.SpeakerDiarization.start_time).all()
    
    return diarizations
