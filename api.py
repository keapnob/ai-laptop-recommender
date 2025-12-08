from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

# 1. INITIALIZE THE APP
app = FastAPI(title="Laptop Recommender API")

# 2. SETUP CORS (Crucial for Next.js)
# This allows your future Frontend (Port 3000) to talk to this Backend (Port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. DATABASE CONNECTION (Same as before)
DATABASE_URL = "postgresql://postgres:newpassword123@127.0.0.1:5440/postgres"
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
model = SentenceTransformer('all-MiniLM-L6-v2')
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
                "name": row[0],
                "price": float(row[1]),
                "specs": row[2],
                "image_url": row[3],  # <--- NEW: Send image to frontend
                "match_score": round(float(row[4]) * 100, 1) # Note: Similarity is now index 4
            })
            
        return {"count": len(results), "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        # C. Format the data as JSON (List of Dictionaries)
        # We don't draw UI here. We just pack the data nicely.
        results = []
        for row in rows:
            results.append({
                "name": row[0],
                "price": float(row[1]),
                "specs": row[2],
                "match_score": round(float(row[3]) * 100, 1) # Convert 0.85 to 85.0
            })
            
        return {"count": len(results), "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))