# 1. Fix the import: Added 'text' to this list
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from config import DATABASE_URL

# 2. Define the Database Connection
engine = create_engine(DATABASE_URL)

class Base(DeclarativeBase):
    pass

# 3. Define the "Laptop" Table Model
class Laptop(Base):
    __tablename__ = "laptops"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float)
    image_url: Mapped[str] = mapped_column(String, nullable=True) # <--- NEW LINE
    specs: Mapped[str] = mapped_column(Text) # Store raw specs like "16GB RAM, 512GB SSD"
    
    # THE SPECIAL PART: This stores the "AI Meaning" of the laptop
    # 384 is the size of the 'all-MiniLM-L6-v2' model (standard efficient embedding model)
    embedding: Mapped[list] = mapped_column(Vector(384)) 

# 4. Run this code to actually create the table in Docker
if __name__ == "__main__":
    print("Connecting to database...")
    # Use raw SQL to enable the extension first
    with engine.connect() as conn:
        # The error happened here because 'text' wasn't imported!
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Create tables
    Base.metadata.create_all(engine)
    print("✅ Success! Table 'laptops' created with Vector support.")