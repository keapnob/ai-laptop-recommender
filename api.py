import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from config import DATABASE_URL, AI_MODEL_NAME


# 1. INITIALIZE THE APP
app = FastAPI(title="Laptop Recommender API")

# 2. SETUP CORS (Crucial for Next.js)
frontend_url = os.getenv("FRONTEND_URL")
origins = ["*"]
if frontend_url:
    origins = [
        frontend_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. DATABASE CONNECTION (Same as before)
# DATABASE_URL imported from config.py

try:
    engine = create_engine(DATABASE_URL)
    # Test connection
    with engine.connect() as conn:
        pass
    print("✅ Database connected successfully")
except Exception as e:
    print(f"❌ Database Connection Error: {e}")

# 4. LOAD AI MODEL (Global variable)
# We load this once when the server starts
print("🧠 Loading AI Model...")
model = SentenceTransformer(AI_MODEL_NAME)
print("✅ AI Model Loaded")

# 5. API ENDPOINTS

@app.get("/")
def read_root():
    return {"status": "Server is running", "message": "Welcome to the AI Laptop API"}

@app.get("/search")
def search_laptops(query: str, max_price: int = 100000, limit: int = 5):
    try:
        # A. Convert Text -> Vector
        query_vector = model.encode(query).tolist()

        # B. SQL Search (Added image_url to SELECT)
        sql = """
        SELECT name, price, specs, image_url,
               1 - (embedding <=> :vector) as similarity
        FROM laptops
        WHERE price <= :max_price
        ORDER BY embedding <=> :vector ASC
        LIMIT :limit;
        """

        with engine.connect() as conn:
            result = conn.execute(
                text(sql), 
                {
                    "vector": str(query_vector), 
                    "max_price": max_price, 
                    "limit": limit
                }
            )
            rows = result.fetchall()

        # C. Format JSON (Now includes image_url)
        results = []
        for row in rows:
            results.append({
                "name": row[0] or "Unknown Laptop",
                "price": float(row[1]) if row[1] is not None else 0.0,
                "specs": row[2] or "",
                "image_url": row[3] or "",  # <--- NEW: Send image to frontend
                "match_score": round(float(row[4]) * 100, 1) if row[4] is not None else 0.0
            })
            
        return {"count": len(results), "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))