from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String)  # Store path to video file
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_filepath = Column(String, nullable=True)
    
    # Relationship with detections
    detections = relationship("Detection", back_populates="video", cascade="all, delete-orphan")

class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    frame_number = Column(Integer)
    x = Column(Float)
    y = Column(Float)
    width = Column(Float)
    height = Column(Float)
    confidence = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with video
    video = relationship("Video", back_populates="detections")