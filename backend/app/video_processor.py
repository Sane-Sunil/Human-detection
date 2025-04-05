import cv2
import numpy as np
import torch
from ultralytics import YOLO
import io
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from . import models
from .database import get_db, engine
import asyncio
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Global variables for model and processing state
model = None
processing_states = {}

def load_model():
    global model
    if model is None:
        try:
            logger.info("Loading YOLO model...")
            model = YOLO('yolov8n.pt')
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {str(e)}", exc_info=True)
            raise

async def get_processing_progress(video_id: int) -> float:
    return processing_states.get(video_id, {}).get('progress', 0)

def process_video(video_id: int, video):
    try:
        # Initialize processing state
        processing_states[video_id] = {'progress': 0, 'status': 'processing'}
        logger.info(f"Starting video processing for video_id: {video_id}")
        
        # Load model if not already loaded
        load_model()
        
        # Start processing in background
        asyncio.create_task(process_video_async(video_id, video.filepath))
    except Exception as e:
        logger.error(f"Error starting video processing: {str(e)}", exc_info=True)
        processing_states[video_id] = {'progress': -1, 'status': 'failed', 'error': str(e)}

async def process_video_async(video_id: int, video_path: str):
    try:
        # Initialize processing state
        processing_states[video_id] = {'progress': 0, 'status': 'processing'}
        
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Failed to open video file")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Create output directory if it doesn't exist
        output_dir = "processed_videos"
        os.makedirs(output_dir, exist_ok=True)
        
        # Create output video writer with forward slashes and H.264 codec
        output_path = os.path.join(output_dir, f"video_{video_id}.mp4").replace("\\", "/")
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Load YOLO model
        model = YOLO('yolov8n.pt')

        frame_number = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Process frame with YOLO
            results = model(frame)
            
            # Draw detections on frame
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = box.cls[0].cpu().numpy()
                    
                    # Only process person detections
                    if class_id == 0:  # 0 is the class ID for person in COCO dataset
                        # Draw bounding box
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                        
                        # Save detection to database
                        async with AsyncSession(engine) as session:
                            detection = models.Detection(
                                video_id=video_id,
                                frame_number=frame_number,
                                x=float(x1),
                                y=float(y1),
                                width=float(x2 - x1),
                                height=float(y2 - y1),
                                confidence=float(confidence)
                            )
                            session.add(detection)
                            await session.commit()

            # Write frame to output video
            out.write(frame)
            
            # Update progress
            frame_number += 1
            progress = (frame_number / total_frames) * 100
            processing_states[video_id]['progress'] = progress
            
            # Update video record with processed file path
            if progress >= 100:
                async with AsyncSession(engine) as session:
                    stmt = select(models.Video).where(models.Video.id == video_id)
                    result = await session.execute(stmt)
                    video = result.scalar_one_or_none()
                    if video:
                        video.processed_filepath = output_path
                        await session.commit()

        # Release resources
        cap.release()
        out.release()
        
        # Update processing state
        processing_states[video_id] = {'progress': 100, 'status': 'completed'}
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}", exc_info=True)
        processing_states[video_id] = {'progress': -1, 'status': 'failed', 'error': str(e)}
        raise 