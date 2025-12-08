import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(page_title="AI Laptop Recommender", layout="wide")

# Connect to your Database (Port 5440)
DATABASE_URL = "postgresql://postgres:newpassword123@127.0.0.1:5440/postgres"
engine = create_engine(DATABASE_URL)

# Load the AI Model (Cached so it doesn't reload every time you click)
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

try:
    model = load_model()
except Exception as e:
    st.error(f"Error loading AI Model: {e}")
    st.stop()

# --- 2. SEARCH FUNCTION ---
def search_laptops(user_query, max_price, limit=5):
    # A. Convert user text to Vector (The "AI Meaning")
    query_vector = model.encode(user_query).tolist()
    
    # B. The Magic SQL Query
    # We search for laptops where:
    # 1. Price is within budget
    # 2. Ordered by "Cosine Distance" (<=>) - closest meaning matches first
    sql = """
    SELECT name, price, specs, 
           1 - (embedding <=> :vector) as similarity
    FROM laptops
    WHERE price <= :max_price
    ORDER BY embedding <=> :vector ASC
    LIMIT :limit;
    """
    
    with engine.connect() as conn:
        # We need to format the vector as a string for Postgres
        result = conn.execute(
            text(sql), 
            {
                "vector": str(query_vector), 
                "max_price": max_price, 
                "limit": limit
            }
        )
        return result.fetchall()

# --- 3. THE USER INTERFACE ---
st.title("💻 AI Personalized Laptop Recommender")
st.markdown("Describe your dream laptop, and I'll find the best matches from **NotebookSpec**.")

# Sidebar for Filters
with st.sidebar:
    st.header("⚙️ Preferences")
    # Dynamic max value based on data? For now, hardcode to 100k
    budget = st.slider("Max Budget (THB)", min_value=10000, max_value=150000, value=35000, step=1000)
    st.info(f"Looking for laptops under **{budget:,} THB**")

# Main Search Bar
query = st.text_input("What do you need?", placeholder="e.g., A gaming laptop with RTX 4050 for playing Cyberpunk")

if query:
    with st.spinner("🧠 AI is thinking..."):
        try:
            # Run the search
            results = search_laptops(query, budget)
            
            if not results:
                st.warning("No laptops found! Try increasing your budget or checking your database.")
            else:
                st.success(f"Found {len(results)} matches!")
                
                # Display results as cards
                for row in results:
                    name = row[0]
                    price = row[1]
                    specs = row[2]
                    score = row[3] if row[3] else 0.0 # AI Confidence Score
                    
                    # Create a nice card layout
                    with st.container():
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            st.metric(label="Price", value=f"฿{price:,.0f}")
                            # Progress bar for match score
                            st.progress(float(score), text=f"Match: {int(score*100)}%")
                            
                        with col2:
                            st.subheader(name)
                            # Clean up specs for display
                            short_specs = specs[:300] + "..." if len(specs) > 300 else specs
                            st.caption(short_specs)
                            
                        st.divider()
        except Exception as e:
            st.error(f"An error occurred: {e}")