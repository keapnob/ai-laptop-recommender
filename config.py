import os

# Central Database Connection URL
raw_db_url = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:newpassword123@127.0.0.1:5440/postgres"
)

# Render/Railway sometimes provides 'postgres://' which SQLAlchemy doesn't support
if raw_db_url and raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url

# AI Embedding Model Configuration
AI_MODEL_NAME = "all-MiniLM-L6-v2"
