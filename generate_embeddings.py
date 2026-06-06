import sys
import io
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from database_setup import Laptop
from config import DATABASE_URL, AI_MODEL_NAME

# Fix Windows encoding issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 1. Connect to Database
engine = create_engine(DATABASE_URL)


def update_embeddings():
    print(f"[AI] Loading AI Model ({AI_MODEL_NAME})...")
    # This downloads a small, fast model optimized for semantic search
    model = SentenceTransformer(AI_MODEL_NAME)

    with Session(engine) as session:
        # 2. Get all laptops
        laptops = session.query(Laptop).all()
        print(f"[DB] Found {len(laptops)} laptops in database.")
        
        count = 0
        for laptop in laptops:
            # Check if embedding is empty or None
            # We use a safe check: if None, empty, or the first number is 0, it needs updating
            if laptop.embedding is None or len(laptop.embedding) == 0 or laptop.embedding[0] == 0.0:
                
                # Create a rich text description for the AI to read
                # We combine Name + Price + Specs to give the AI full context
                text_to_embed = f"{laptop.name}. Price: {laptop.price} THB. Specs: {laptop.specs}"
                
                # 3. The Magic: Convert Text -> Vector
                vector = model.encode(text_to_embed).tolist()
                
                # 4. Save back to DB
                laptop.embedding = vector
                count += 1
                
                if count % 10 == 0:
                    print(f"   [PROGRESS] Processed {count} laptops...")

        session.commit()
        print(f"[SUCCESS] Updated AI memory for {count} laptops.")

if __name__ == "__main__":
    update_embeddings()