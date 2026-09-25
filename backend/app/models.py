from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Craftsman(Base):
    __tablename__ = "craftsmen"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    school = Column(String(100), nullable=False)
    generation = Column(Integer)
    bio = Column(Text)
    avatar = Column(String(255))
    contact = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="craftsman")
    transcripts = relationship("Transcript", back_populates="craftsman")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    craftsman_id = Column(Integer, ForeignKey("craftsmen.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    message_type = Column(String(50), default="chat")

    craftsman = relationship("Craftsman", back_populates="messages")


class AudioRecording(Base):
    __tablename__ = "audio_recordings"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_path = Column(String(255), nullable=False)
    processed_path = Column(String(255))
    duration = Column(Float)
    workshop = Column(String(100))
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="uploaded")

    transcripts = relationship("Transcript", back_populates="recording")
    diarizations = relationship("SpeakerDiarization", back_populates="recording")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("audio_recordings.id"))
    craftsman_id = Column(Integer, ForeignKey("craftsmen.id"))
    content = Column(Text, nullable=False)
    start_time = Column(Float)
    end_time = Column(Float)
    language = Column(String(10), default="zh")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recording = relationship("AudioRecording", back_populates="transcripts")
    craftsman = relationship("Craftsman", back_populates="transcripts")
    keywords = relationship("TranscriptKeyword", back_populates="transcript")


class SpeakerDiarization(Base):
    __tablename__ = "speaker_diarizations"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("audio_recordings.id"))
    speaker_label = Column(String(50), nullable=False)
    start_time = Column(Float)
    end_time = Column(Float)
    predicted_school = Column(String(100))
    confidence = Column(Float)

    recording = relationship("AudioRecording", back_populates="diarizations")


class TranscriptKeyword(Base):
    __tablename__ = "transcript_keywords"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"))
    keyword = Column(String(100), nullable=False)
    category = Column(String(50))
    importance = Column(Float, default=1.0)

    transcript = relationship("Transcript", back_populates="keywords")


class CraftArchive(Base):
    __tablename__ = "craft_archives"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(JSON)
    keywords = Column(JSON)
    related_transcript_ids = Column(JSON)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_to_feiyi = Column(Integer, default=0)
    sent_at = Column(DateTime(timezone=True))


class WoodMaterial(Base):
    __tablename__ = "wood_materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    scientific_name = Column(String(100))
    origin = Column(String(255))
    description = Column(Text)
    texture_image = Column(String(255))
    suitable_parts = Column(JSON)
    properties = Column(JSON)
    traditional_usage = Column(Text)


class BowPart(Base):
    __tablename__ = "bow_parts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    traditional_name = Column(String(100))
    description = Column(Text)
    diagram_coords = Column(JSON)
    materials = Column(JSON)
    crafting_steps = Column(JSON)
