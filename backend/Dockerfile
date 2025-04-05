FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Create setup script
RUN echo '#!/bin/bash\n\
if [ ! -f "/app/.initialized" ]; then\n\
    if [ ! -d "alembic" ]; then\n\
        alembic init alembic\n\
    fi\n\
    alembic revision --autogenerate -m "update_video_model"\n\
    alembic upgrade head\n\
    touch /app/.initialized\n\
fi' > /app/setup.sh && \
chmod +x /app/setup.sh

# Create startup script
RUN echo '#!/bin/bash\n\
/app/setup.sh\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload' > /app/start.sh && \
chmod +x /app/start.sh

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["/app/start.sh"]