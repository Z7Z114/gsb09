from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


def _require_non_blank(value: str) -> str:
    """必填字符串：去除首尾空白后必须非空，返回值已规整。"""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("不能为空或仅包含空白字符")
    return value.strip()


class CraftsmanBase(BaseModel):
    name: str
    school: str
    generation: Optional[int] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    contact: Optional[str] = None

    @field_validator("name", "school")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class CraftsmanCreate(CraftsmanBase):
    pass


class Craftsman(CraftsmanBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    content: str
    craftsman_id: Optional[int] = None
    message_type: str = "chat"

    @field_validator("content")
    @classmethod
    def _content_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    timestamp: datetime
    craftsman: Optional[Craftsman] = None

    class Config:
        from_attributes = True


class AudioRecordingBase(BaseModel):
    filename: str
    workshop: Optional[str] = None


class AudioRecordingCreate(AudioRecordingBase):
    original_path: str


class AudioRecording(AudioRecordingBase):
    id: int
    original_path: str
    processed_path: Optional[str] = None
    duration: Optional[float] = None
    recorded_at: datetime
    status: str

    class Config:
        from_attributes = True


class TranscriptBase(BaseModel):
    recording_id: int
    craftsman_id: Optional[int] = None
    content: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    language: str = "zh"


class TranscriptCreate(TranscriptBase):
    pass


class Transcript(TranscriptBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SpeakerDiarizationBase(BaseModel):
    recording_id: int
    speaker_label: str
    start_time: float
    end_time: float
    predicted_school: Optional[str] = None
    confidence: Optional[float] = None


class SpeakerDiarizationCreate(SpeakerDiarizationBase):
    pass


class SpeakerDiarization(SpeakerDiarizationBase):
    id: int

    class Config:
        from_attributes = True


class CraftArchiveBase(BaseModel):
    title: str
    summary: str
    content: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    related_transcript_ids: Optional[List[int]] = None


class CraftArchiveCreate(CraftArchiveBase):
    pass


class CraftArchive(CraftArchiveBase):
    id: int
    generated_at: datetime
    sent_to_feiyi: int
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WoodMaterialBase(BaseModel):
    name: str
    scientific_name: Optional[str] = None
    origin: Optional[str] = None
    description: Optional[str] = None
    texture_image: Optional[str] = None
    suitable_parts: Optional[List[str]] = None
    properties: Optional[Dict[str, Any]] = None
    traditional_usage: Optional[str] = None

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class WoodMaterialCreate(WoodMaterialBase):
    pass


class WoodMaterial(WoodMaterialBase):
    id: int

    class Config:
        from_attributes = True


class BowPartBase(BaseModel):
    name: str
    traditional_name: Optional[str] = None
    description: Optional[str] = None
    diagram_coords: Optional[Dict[str, Any]] = None
    materials: Optional[List[str]] = None
    crafting_steps: Optional[List[Dict[str, Any]]] = None

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class BowPartCreate(BowPartBase):
    pass


class BowPart(BowPartBase):
    id: int

    class Config:
        from_attributes = True


class AudioProcessResponse(BaseModel):
    recording_id: int
    status: str
    message: str


class ArchiveEmailRequest(BaseModel):
    archive_id: int
    recipient_email: Optional[str] = None
    custom_message: Optional[str] = None
