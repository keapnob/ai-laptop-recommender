import sys
import io
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from database_setup import Laptop, Base

LOCAL_DATABASE_URL = "postgresql://postgres:newpassword123@127.0.0.1:5440/postgres"
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_V8IzFfvirCY2@ep-cool-dust-aomwty90.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Fix Windows encoding issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def migrate():
    print("Connecting to databases...")
    local_engine = create_engine(LOCAL_DATABASE_URL)
    neon_engine = create_engine(NEON_DATABASE_URL)
    
    # 1. Enable extension and create tables on Neon
    print("Setting up pgvector extension on Neon...")
    with neon_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    print("Creating tables on Neon...")
    Base.metadata.create_all(neon_engine)
    
    # 2. Fetch all laptops from Local
    print("Fetching laptops from local database...")
    with Session(local_engine) as local_session:
        laptops = local_session.query(Laptop).all()
        print(f"Found {len(laptops)} laptops locally.")
        
        if not laptops:
            print("No laptops found locally to migrate!")
            return
            
        # 3. Insert into Neon
        print("Inserting laptops into Neon...")
        with Session(neon_engine) as neon_session:
            # Clear existing to avoid duplicate conflicts
            neon_session.execute(text("TRUNCATE TABLE laptops RESTART IDENTITY"))
            
            for laptop in laptops:
                new_laptop = Laptop(
                    name=laptop.name,
                    price=laptop.price,
                    specs=laptop.specs,
                    image_url=laptop.image_url,
                    embedding=laptop.embedding
                )
                neon_session.add(new_laptop)
            
            neon_session.commit()
            print("✅ Migration completed successfully!")

if __name__ == "__main__":
    migrate()
