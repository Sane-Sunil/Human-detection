# Human Detection in video

A full-stack application for video processing and analysis using React for the frontend and Python for the backend. The application uses YOLOv8 for object detection and processing. I haven't hosted it on any platform since the model takes hours for the processing even in my PC. After processing the tracking in it is good i think (check the test_video.mp4).

If anyone can improve the project, then by all means you are welcome☺️.

## Project Structure

```
.
├── frontend/          # React frontend application
├── backend/          # FastAPI backend application
└── README.md
```

## Prerequisites

- Node.js (v14 or higher)
- Python 3.11
- PostgreSQL database
- Docker (optional, for containerized deployment)

## Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python3.11 -m venv .venv #Or use python 3.11 path
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the backend directory with the following variables:
   ```
   DATABASE_URL=your_database_url
   UPLOAD_DIR=uploads
   MODEL_DIR=models
   ```

5. Initialize the database:
      
    ```bash 
    alembic init alembic
    alembic revision --autogenerate -m "Update video model to use binary storage" #Whatever this is supposed to be
    alembic upgrade head
    ```

6. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

The backend will be available at `http://localhost:8000`

## Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`

## Docker Deployment

(If it works it works, but most probably it won't)

### Using Dockerfile

#### Backend

1. Build the Docker image:
   ```bash
   cd backend
   docker build -t video-processing-backend .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/models:/app/models video-processing-backend
   ```

#### Frontend

1. Build the Docker image:
   ```bash
   cd frontend
   docker build -t video-processing-frontend .
   ```

2. Run the container:
   ```bash
   docker run -p 3000:3000 video-processing-frontend
   ```

### Docker Compose

1. Create a `docker-compose.yml` file in the root directory:
   ```yaml
   version: '3.8'
   services:
     backend:
       build: ./backend
       ports:
         - "8000:8000"
       volumes:
         - ./backend:/app
         - ./uploads:/app/uploads
         - ./processed_videos:/app/processed_videos
         - backend_data:/app
       environment:
         - DATABASE_URL=YOUR_DB_URL #Change it if you care
         - PYTHONUNBUFFERED=1
         - MODEL_PATH=/app/yolov8n.pt
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
         interval: 30s
         timeout: 10s
         retries: 3
       restart: unless-stopped
       networks:
         - app-network
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
     frontend:
       build: ./frontend
       ports:
         - "3000:3000"
       volumes:
         - ./frontend:/app
         - /app/node_modules
       environment:
         - REACT_APP_API_URL=http://backend:8000
         - NODE_ENV=development
       depends_on:
         - backend
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:3000"]
         interval: 30s
         timeout: 10s
         retries: 3
       restart: unless-stopped
       networks:
         - app-network
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
   volumes:
     backend_data:
       driver: local
   networks:
     app-network:
       driver: bridge
   ```

2. Build the images:
   ```bash
   docker compose build
   ```

3. Run containers:
   ```bash
   docker compose up
   ```

___Note:___
If you have followed correctly to set up this app with docker and finished building it, you will see that it doesn't work.

## Features

- Video upload and processing
- Object detection using YOLOv8
- RESTful API backend
- PostgreSQL database integration

## API Documentation

Once the backend is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables

The following environment variables need to be set in the backend's `.env` file:

- `DATABASE_URL`: PostgreSQL database connection string in the format:
  ```
  postgresql+asyncpg://username:password@host:port/database_name
  ```
  Example:
  ```
  DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/video_db
  ```

- `UPLOAD_DIR`: Directory where uploaded videos will be stored (default: "uploads")
  ```
  UPLOAD_DIR=uploads
  ```

- `MODEL_DIR`: Directory where YOLO model files are stored (default: "models")
  ```
  MODEL_DIR=models
  ```

Note: Make sure to create these directories (uploads and models) in your backend folder before starting the application.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Good Bad & Evil'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.