from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class VideoBase(BaseModel):
    filename: str
    filepath: Optional[str] = None

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DetectionBase(BaseModel):
    video_id: int
    frame_number: int
    x: float
    y: float
    width: float
    height: float
    confidence: float

class DetectionCreate(DetectionBase):
    pass

class Detection(DetectionBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True 