import re
import time
from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from database_setup import Laptop

# Connect to Database (Port 5440)
DATABASE_URL = "postgresql://postgres:newpassword123@127.0.0.1:5440/postgres"
engine = create_engine(DATABASE_URL)

def clean_price(price_str):
    """Extracts numbers from messy strings like 'Starts at ฿ 25,900'"""
    if not price_str: return 0.0
    clean = re.sub(r'[^\d]', '', price_str)
    try:
        return float(clean)
    except:
        return 0.0

def scrape_notebookspec_pro():
    print("🚀 Starting 'Pro' Scraper (with Images)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        url = "https://notebookspec.com/notebook/search?order=latest"
        print(f"🌍 Navigating to {url}...")
        page.goto(url)

        # 1. Close Cookies if present
        try:
            page.locator("text=ยอมรับ").click(timeout=2000)
        except:
            pass

        # 2. Scroll A LOT (Load ~100 items)
        print("⬇️ Scrolling to load inventory...")
        for i in range(15): 
            page.mouse.wheel(0, 5000)
            time.sleep(1)

        # 3. Find Anchors
        anchors = page.locator("text=เปรียบเทียบ").all()
        print(f"🔍 Found {len(anchors)} potential laptops.")

        data_list = []
        
        for i, anchor in enumerate(anchors):
            try:
                # 4. SMART PARENT FINDER
                card = anchor.locator("xpath=../../..") # Try 3 levels up
                
                # Check if this valid card has a title?
                title_el = card.locator(".title")
                if title_el.count() == 0:
                    card = anchor.locator("xpath=../../../..") # Try 4 levels up
                    title_el = card.locator(".title")

                # 5. Extract Data
                if title_el.count() > 0:
                    name = title_el.first.inner_text().strip()
                    
                    # Find Price
                    price_el = card.locator(".price")
                    if price_el.count() > 0:
                        price_text = price_el.first.inner_text()
                    else:
                        price_text = card.inner_text()
                    
                    price = clean_price(price_text)
                    
                    # --- [NEW] IMAGE EXTRACTOR ---
                    img_el = card.locator("img").first
                    img_url = "https://notebookspec.com/web/img/default_notebook_search.jpg" # Fallback
                    
                    if img_el.count() > 0:
                        src = img_el.get_attribute("src")
                        if src:
                            img_url = src
                    # -----------------------------

                    # --- [UPDATED] SPECS EXTRACTOR ---
                    specs_el = card.locator(".detail")
                    if specs_el.count() > 0:
                        specs = specs_el.first.inner_text().replace("\n", ", ")
                    else:
                        # Fallback: Grab all text, remove Name/Price to leave just specs
                        full_text = card.inner_text().replace("\n", " ")
                        specs = full_text.replace(name, "").replace(price_text, "").replace("เปรียบเทียบ", "").strip()
                    
                    if len(specs) < 10:
                         specs = "Specs found in title: " + name
                    # ---------------------------------

                    # 6. Save valid items
                    if price > 5000:
                        item = {
                            "name": name,
                            "price": price,
                            "specs": specs[:500],
                            "image_url": img_url,  # <--- Saved here
                            "embedding": [0.0] * 384
                        }
                        
                        # Deduplicate
                        if not any(d['name'] == name for d in data_list):
                            data_list.append(item)
                            print(f"   ✅ [{i+1}/{len(anchors)}] Scraped: {name[:20]}... | {price} THB")
                    else:
                        print(f"   ⚠️ [{i+1}] Skipped: Price too low ({price})")
                else:
                    print(f"   ⚠️ [{i+1}] Skipped: Could not find Title inside card")

            except Exception as e:
                print(f"   ❌ Error on item {i+1}: {e}")
                continue

        browser.close()
        return data_list

def save_to_db(data):
    if not data: return
    print(f"💾 Saving {len(data)} laptops to Database...")
    with Session(engine) as session:
        count = 0
        for item in data:
            exists = session.execute(text("SELECT id FROM laptops WHERE name = :n"), {"n": item["name"]}).fetchone()
            if not exists:
                new_laptop = Laptop(
                    name=item["name"],
                    price=item["price"],
                    specs=item["specs"],
                    image_url=item["image_url"],  # <--- Saved to DB
                    embedding=item["embedding"]
                )
                session.add(new_laptop)
                count += 1
        session.commit()
    print(f"🎉 SUCCESS! Added {count} new laptops to your database.")

if __name__ == "__main__":
    data = scrape_notebookspec_pro()
    save_to_db(data)