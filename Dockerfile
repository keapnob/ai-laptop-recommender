FROM python:3.10-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /code

# Install system dependencies (like build-essential, g++ if needed, but psycopg2-binary handles postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Pre-download the SentenceTransformer AI model during Docker build
# This makes container startup much faster on Hugging Face Spaces
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the rest of the application files
COPY api.py /code/api.py
COPY config.py /code/config.py
COPY database_setup.py /code/database_setup.py

# Expose port 7860 (Hugging Face Spaces default port)
EXPOSE 7860

# Run FastAPI using uvicorn on port 7860
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
