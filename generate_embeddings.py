from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from database_setup import Laptop

# 1. Connect to Database (Port 5440)
DATABASE_URL = "postgresql://postgres:newpassword123@127.0.0.1:5440/postgres"
engine = create_engine(DATABASE_URL)

def update_embeddings():
    print("🧠 Loading AI Model (all-MiniLM-L6-v2)...")
    # This downloads a small, fast model optimized for semantic search
    model = SentenceTransformer('all-MiniLM-L6-v2')

    with Session(engine) as session:
        # 2. Get all laptops
        laptops = session.query(Laptop).all()
        print(f"📂 Found {len(laptops)} laptops in database.")
        
        count = 0
        for laptop in laptops:
            # Check if embedding is empty (sum is 0)
            # We use a simple check: if the first number is 0, it probably needs updating
            if laptop.embedding[0] == 0.0:
                
                # Create a rich text description for the AI to read
                # We combine Name + Price + Specs to give the AI full context
                text_to_embed = f"{laptop.name}. Price: {laptop.price} THB. Specs: {laptop.specs}"
                
                # 3. The Magic: Convert Text -> Vector
                vector = model.encode(text_to_embed).tolist()
                
                # 4. Save back to DB
                laptop.embedding = vector
                count += 1
                
                if count % 10 == 0:
                    print(f"   ⚡ Processed {count} laptops...")

        session.commit()
        print(f"✅ Success! Updated AI memory for {count} laptops.")

if __name__ == "__main__":
    update_embeddings()