# AI-Powered Laptop Recommender (RAG)

> A Full-Stack AI application that uses **Retrieval-Augmented Generation (RAG)** to recommend laptops based on natural language queries (e.g., *"I need a laptop for heavy gaming and coding under 35k"*).

 Architecture

This project uses a decoupled **Microservices Architecture**:

* **Data Pipeline:** Scrapes real-time data and generates embeddings.
* **Database:** PostgreSQL with `pgvector` for semantic similarity search.
* **Backend:** FastAPI handles the search logic and API routing.
* **Frontend:** Next.js provides a responsive, dark-mode user interface.

##  Tech Stack

* **Frontend:** Next.js 14 (React), Tailwind CSS, TypeScript
* **Backend API:** Python (FastAPI), Uvicorn
* **Database:** PostgreSQL (Dockerized) with `pgvector` extension
* **AI & ML:** `sentence-transformers` (HuggingFace), Vector Embeddings
* **Data Engineering:** Playwright (Web Scraping), SQLAlchemy

## Key Features

*  Semantic Search:** Understands user intent (e.g., "multitasking" maps to high RAM/CPU) using Vector Embeddings rather than just exact keyword matches.
*  Real-Time Data:** Custom-built web scraper extracts real-time prices and specs from Thai e-commerce sites.
*  Hybrid Filtering:** Combines AI vector search with hard SQL filters (Price, Availability).
*  Modern UI:** Responsive interface built with Next.js and Tailwind.

##  Installation & Setup

### 1. Database Setup (Docker)
```bash
docker-compose up -d
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt

# 2 .Run Pipeline
python database_setup.py      
python scraper_nbs_pro.py     
python generate_embeddings.py 

# 3. Start API
uvicorn api:app --reload
cd frontend
npm install
npm run dev
# 4. **Stage the change:**
   ```bash
   git add README.md
#5. Commit the change with a message:
git commit -m "Add detailed README documentation"
Push to GitHub:
