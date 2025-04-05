from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from . import models, schemas
from .database import engine, Base, get_db, AsyncSessionLocal, init_db
from .video_processor import process_video, get_processing_progress
import os
from dotenv import load_dotenv
import logging
import io
from typing import List
import asyncio
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Create directories if they don't exist
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("Database initialized")

@app.post("/video/upload")
async def upload_video(file: UploadFile = File(...)):
    try:
        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Save file to disk
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create video record
        video = models.Video(
            filename=file.filename,
            filepath=filepath,
            created_at=datetime.now()
        )
        
        async with AsyncSession(engine) as session:
            session.add(video)
            await session.commit()
            await session.refresh(video)
            
            # Start processing in background
            process_video(video.id, video)
            
            return {
                "id": video.id,
                "filename": video.filename,
                "created_at": video.created_at.isoformat()
            }
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos")
async def get_videos():
    try:
        async with AsyncSession(engine) as session:
            stmt = select(models.Video)
            result = await session.execute(stmt)
            videos = result.scalars().all()
            return [{
                "id": v.id,
                "filename": v.filename,
                "created_at": v.created_at.isoformat() if v.created_at else None
            } for v in videos]
    except Exception as e:
        logger.error(f"Error fetching videos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/{video_id}/status")
async def get_video_status(video_id: int):
    try:
        async with AsyncSession(engine) as session:
            # Check if video exists
            stmt = select(models.Video).where(models.Video.id == video_id)
            result = await session.execute(stmt)
            video = result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            # Check if video has detections
            stmt = select(models.Detection).where(models.Detection.video_id == video_id)
            result = await session.execute(stmt)
            detections = result.scalars().all()
            
            if detections:
                return {"status": "completed", "progress": 100}
            
            # Get processing progress
            progress = get_processing_progress(video_id)
            if progress == -1:
                return {"status": "failed", "progress": 0}
            elif progress > 0:
                return {"status": "processing", "progress": progress}
            else:
                return {"status": "pending", "progress": 0}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/{video_id}")
async def get_video(video_id: int):
    try:
        async with AsyncSession(engine) as session:
            # Check if video exists
            stmt = select(models.Video).where(models.Video.id == video_id)
            result = await session.execute(stmt)
            video = result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            return {
                "id": video.id,
                "filename": video.filename,
                "created_at": video.created_at.isoformat() if video.created_at else None
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/video/{video_id}/process")
async def process_video_endpoint(video_id: int):
    try:
        async with AsyncSession(engine) as session:
            # Check if video exists
            stmt = select(models.Video).where(models.Video.id == video_id)
            result = await session.execute(stmt)
            video = result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            # Check if video is already processed
            stmt = select(models.Detection).where(models.Detection.video_id == video_id)
            result = await session.execute(stmt)
            detections = result.scalars().all()
            
            if detections:
                return {"status": "completed", "message": "Video already processed"}
            
            # Start processing
            process_video(video_id, video)
            return {"status": "processing", "message": "Video processing started"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting video processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/detections/{video_id}")
async def get_detections(video_id: int):
    try:
        async with AsyncSession(engine) as session:
            # Check if video exists
            stmt = select(models.Video).where(models.Video.id == video_id)
            result = await session.execute(stmt)
            video = result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            # Get detections
            stmt = select(models.Detection).where(models.Detection.video_id == video_id)
            result = await session.execute(stmt)
            detections = result.scalars().all()
            
            if not detections:
                raise HTTPException(status_code=404, detail="No detections found for this video")
            
            return [{
                "id": d.id,
                "frame_number": d.frame_number,
                "confidence": d.confidence,
                "x": d.x,
                "y": d.y,
                "width": d.width,
                "height": d.height,
                "timestamp": d.timestamp.isoformat()
            } for d in detections]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching detections: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/video/{video_id}")
async def delete_video(video_id: int):
    try:
        async with AsyncSession(engine) as session:
            # Check if video exists
            stmt = select(models.Video).where(models.Video.id == video_id)
            result = await session.execute(stmt)
            video = result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            # Delete video file
            if os.path.exists(video.filepath):
                os.remove(video.filepath)
            
            # Delete processed video file if exists
            if video.processed_filepath and os.path.exists(video.processed_filepath):
                os.remove(video.processed_filepath)
            
            # Delete all detections first
            stmt = delete(models.Detection).where(models.Detection.video_id == video_id)
            await session.execute(stmt)
            
            # Delete video
            await session.delete(video)
            await session.commit()
            
            return {"message": "Video and associated detections deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/{video_id}/processed")
async def get_processed_video(video_id: int):
    try:
        async with AsyncSession(engine) as session:
            # Check if video exists
            stmt = select(models.Video).where(models.Video.id == video_id)
            result = await session.execute(stmt)
            video = result.scalar_one_or_none()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            if not video.processed_filepath:
                raise HTTPException(status_code=404, detail="Processed video not found")
            
            # Convert path to use forward slashes
            processed_path = video.processed_filepath.replace("\\", "/")
            
            if not os.path.exists(processed_path):
                logger.error(f"Processed video file not found at path: {processed_path}")
                raise HTTPException(status_code=404, detail="Processed video file not found")
            
            # Return the processed video file with proper headers
            return FileResponse(
                processed_path,
                media_type="video/mp4",
                filename=f"processed_{video.filename}",
                headers={
                    "Content-Disposition": f'attachment; filename="processed_{video.filename}"',
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(os.path.getsize(processed_path)),
                    "Cache-Control": "no-cache"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving processed video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 