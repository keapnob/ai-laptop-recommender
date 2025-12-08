import re
import time
from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from database_setup import Laptop

# Database Config
DATABASE_URL = "postgresql://postgres:newpassword123@127.0.0.1:5440/postgres"
engine = create_engine(DATABASE_URL)

def clean_price(text_list):
    """Finds the price in a list of text lines"""
    for line in text_list:
        # Look for numbers that look like prices (e.g., 25,900)
        # Must have a comma and be at least 4 digits
        if ',' in line and any(char.isdigit() for char in line):
            clean = re.sub(r'[^\d]', '', line)
            try:
                val = float(clean)
                # Sanity check: Laptops usually cost more than 5000
                if val > 5000:
                    return val
            except:
                continue
    return 0.0

def scrape_notebookspec_anchor():
    print("🚀 Starting 'Anchor' Scraper (Target: 'เปรียบเทียบ')...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # URL: We add '?order=latest' to force the list to load fresh items
        url = "https://notebookspec.com/notebook/search?order=latest"
        print(f"🌍 Navigating to {url}...")
        page.goto(url)

        # 1. Wait for the "Compare" buttons to appear
        try:
            # "เปรียบเทียบ" = Compare in Thai
            page.wait_for_selector("text=เปรียบเทียบ", timeout=15000)
        except:
            print("❌ Could not find any 'Compare' buttons. Site might have changed.")
            return []

        # 2. Scroll to load more
        print("⬇️ Scrolling...")
        for i in range(5):
            page.mouse.wheel(0, 4000)
            time.sleep(1.5)

        # 3. Find all "Compare" buttons
        print("⚓ finding Anchors...")
        # We find the label containing the text
        anchors = page.locator("text=เปรียบเทียบ").all()
        print(f"🔍 Found {len(anchors)} laptops via Anchors.")

        data_list = []
        
        for anchor in anchors:
            try:
                # The Anchor is inside the Card. 
                # We go up 3-4 levels to get the whole Card Box.
                # Anchor -> Checkbox Wrapper -> Card Footer -> Card Body -> Card
                card = anchor.locator("..").locator("..").locator("..").locator("..")
                
                # Get all text in the card
                text_content = card.inner_text().split('\n')
                
                # Extract Name (Usually the longest line near the top)
                name = "Unknown"
                for line in text_content[:5]: # Look at first 5 lines for name
                    if len(line) > 15: 
                        name = line
                        break
                
                # Extract Price (Find the number)
                price = clean_price(text_content)

                # Extract Specs (Everything else)
                specs = " ".join(text_content).replace(name, "").replace("เปรียบเทียบ", "")

                if name != "Unknown" and price > 0:
                    item = {
                        "name": name,
                        "price": price,
                        "specs": specs[:500],
                        "embedding": [0.0] * 384
                    }
                    
                    # Prevent duplicates
                    if not any(d['name'] == name for d in data_list):
                        data_list.append(item)
                        print(f"   ✅ Scraped: {name[:30]}... | {price} THB")

            except Exception as e:
                continue

        browser.close()
        return data_list

def save_to_db(data):
    if not data: 
        print("⚠️ No valid laptops found.")
        return

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
                    embedding=item["embedding"]
                )
                session.add(new_laptop)
                count += 1
        session.commit()
    print(f"🎉 SUCCESS! Added {count} new laptops to your database.")

if __name__ == "__main__":
    data = scrape_notebookspec_anchor()
    save_to_db(data)