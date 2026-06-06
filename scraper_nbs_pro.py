import re
import time
import sys
import io
from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from database_setup import Laptop

from config import DATABASE_URL

# Fix Windows encoding issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Connect to Database
engine = create_engine(DATABASE_URL)

# ============================================================
# CONFIGURATION
# ============================================================
MAX_PAGES = 200          # Safety limit
SCROLL_PER_PAGE = 25     # Max scroll rounds per page
SCROLL_WAIT = 0.8        # Seconds between scrolls
PAGE_LOAD_WAIT = 3       # Seconds after page navigation
RETRY_ATTEMPTS = 3

BASE_URL = "https://notebookspec.com/notebook/search"


def clean_price(price_str):
    """Extracts numbers from messy strings like 'Starts at 25,900'"""
    if not price_str: return 0.0
    clean = re.sub(r'[^\d]', '', price_str)
    try:
        return float(clean)
    except:
        return 0.0


def smart_scroll(page, max_scrolls=SCROLL_PER_PAGE):
    """Scroll until no new items load or max_scrolls reached"""
    previous_count = 0
    no_change_count = 0

    for i in range(max_scrolls):
        page.mouse.wheel(0, 5000)
        time.sleep(SCROLL_WAIT)

        current_count = page.locator("text=เปรียบเทียบ").count()

        if current_count == previous_count:
            no_change_count += 1
            if no_change_count >= 3:
                break
        else:
            no_change_count = 0

        previous_count = current_count

    final_count = page.locator("text=เปรียบเทียบ").count()
    return final_count


def extract_laptops_from_page(page, seen_names):
    """Extract all laptop data from current page, skip already-seen names"""
    anchors = page.locator("text=เปรียบเทียบ").all()
    page_data = []

    for i, anchor in enumerate(anchors):
        try:
            # SMART PARENT FINDER
            card = anchor.locator("xpath=../../..")
            title_el = card.locator(".title")
            if title_el.count() == 0:
                card = anchor.locator("xpath=../../../..")
                title_el = card.locator(".title")

            if title_el.count() > 0:
                name = title_el.first.inner_text().strip()

                # Skip duplicates early
                if name in seen_names:
                    continue

                # Find Price
                price_el = card.locator(".price")
                if price_el.count() > 0:
                    price_text = price_el.first.inner_text()
                else:
                    price_text = card.inner_text()
                price = clean_price(price_text)

                # IMAGE EXTRACTOR
                img_el = card.locator("img").first
                img_url = "https://notebookspec.com/web/img/default_notebook_search.jpg"
                if img_el.count() > 0:
                    src = img_el.get_attribute("src")
                    if src:
                        img_url = src

                # SPECS EXTRACTOR
                specs_el = card.locator(".detail")
                if specs_el.count() > 0:
                    specs = specs_el.first.inner_text().replace("\n", ", ")
                else:
                    full_text = card.inner_text().replace("\n", " ")
                    specs = full_text.replace(name, "").replace(price_text, "").replace("เปรียบเทียบ", "").strip()

                if len(specs) < 10:
                    specs = "Specs found in title: " + name

                if price > 5000:
                    item = {
                        "name": name,
                        "price": price,
                        "specs": specs[:500],
                        "image_url": img_url,
                        "embedding": [0.0] * 384
                    }
                    page_data.append(item)
                    seen_names.add(name)

        except Exception as e:
            continue

    return page_data


def click_next_page(page):
    """Try to click the 'Next Page' button on NotebookSpec. Returns True if successful."""

    # Strategy 1: Look for a ">" or ">>" or "Next" arrow button in pagination
    # NotebookSpec uses Livewire pagination with page number buttons
    try:
        # Scroll to bottom to make pagination visible
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)

        # Look for pagination container - common patterns
        # Try: aria-label="Next", rel="next", text ">", text "Next"
        next_selectors = [
            'a[rel="next"]',
            'button[rel="next"]',
            'a[aria-label="Next"]',
            'button[aria-label="Next"]',
            'li.page-item:last-child a',
            '.pagination a:has-text(">")',
            '.pagination a:has-text("Next")',
            'nav a:has-text(">")',
            # Livewire specific
            'button[wire\\:click*="nextPage"]',
            'button[wire\\:click*="gotoPage"]',
        ]

        for selector in next_selectors:
            try:
                el = page.locator(selector).first
                if el.count() > 0 and el.is_visible():
                    el.click()
                    time.sleep(PAGE_LOAD_WAIT)
                    return True
            except:
                continue

        # Strategy 2: Find all pagination page numbers and click the next one
        # Look for active page number, then click the one after it
        try:
            # Find all page links in pagination
            pagination_links = page.locator('.pagination a, nav[role="navigation"] a').all()
            
            if pagination_links:
                # Find which link has "active" class or is the current page
                found_active = False
                for link in pagination_links:
                    try:
                        link_text = link.inner_text().strip()
                        parent_class = link.locator("..").get_attribute("class") or ""
                        
                        if found_active:
                            # This is the next page link - click it
                            if link_text.isdigit():
                                link.click()
                                time.sleep(PAGE_LOAD_WAIT)
                                return True
                        
                        if "active" in parent_class or "current" in parent_class:
                            found_active = True
                    except:
                        continue
        except:
            pass

        # Strategy 3: Use keyboard shortcut or evaluate Livewire
        try:
            # Try clicking using Livewire wire:click
            livewire_buttons = page.locator('[wire\\:click]').all()
            for btn in livewire_buttons:
                try:
                    wire_click = btn.get_attribute("wire:click")
                    if wire_click and ("nextPage" in wire_click or "gotoPage" in wire_click):
                        btn.click()
                        time.sleep(PAGE_LOAD_WAIT)
                        return True
                except:
                    continue
        except:
            pass

        return False

    except Exception as e:
        print(f"   [WARN] Error clicking next: {e}")
        return False


def scrape_all_pages():
    """Scrape all pages of NotebookSpec by clicking pagination buttons"""
    print("[START] Starting Full Scraper (All Pages + Images)...")
    print(f"   Config: max {MAX_PAGES} pages, {SCROLL_PER_PAGE} scrolls/page")
    print("=" * 60)

    all_data = []
    seen_names = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Navigate to the search page
        print(f"\n[NAVIGATE] Opening {BASE_URL}")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(PAGE_LOAD_WAIT)

        # Close cookies popup
        try:
            page.locator("text=ยอมรับ").click(timeout=3000)
            print("   [OK] Closed cookie popup")
        except:
            pass

        for page_num in range(1, MAX_PAGES + 1):
            print(f"\n--- PAGE {page_num} ---")

            # Scroll to load all items on this page
            print(f"   [SCROLL] Loading items...")
            total_on_page = smart_scroll(page)
            print(f"   [FOUND] {total_on_page} items visible on page")

            if total_on_page == 0:
                print(f"   [END] No items found. Stopping.")
                break

            # Extract data
            page_data = extract_laptops_from_page(page, seen_names)
            print(f"   [OK] Extracted {len(page_data)} new laptops (Total: {len(all_data) + len(page_data)})")

            all_data.extend(page_data)

            # If no new laptops found, we might have reached the end
            if len(page_data) == 0:
                print(f"   [END] No new laptops found. All unique data scraped!")
                break

            # Try to go to next page by clicking pagination button
            print(f"   [NEXT] Clicking next page...")

            # Scroll back to top first for clean state
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)

            if not click_next_page(page):
                print(f"   [END] No 'Next' button found. This was the last page!")
                break

            # Wait for new content to load
            time.sleep(2)

            # Scroll back to top for the new page
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)

        browser.close()

    print("\n" + "=" * 60)
    print(f"[TOTAL] Scraped {len(all_data)} unique laptops from NotebookSpec!")
    print("=" * 60)
    return all_data


def save_to_db(data):
    if not data:
        print("[WARN] No valid laptops found.")
        return

    print(f"\n[SAVE] Saving {len(data)} laptops to Database...")
    with Session(engine) as session:
        count = 0
        for item in data:
            exists = session.execute(
                text("SELECT id FROM laptops WHERE name = :n"),
                {"n": item["name"]}
            ).fetchone()

            if not exists:
                new_laptop = Laptop(
                    name=item["name"],
                    price=item["price"],
                    specs=item["specs"],
                    image_url=item["image_url"],
                    embedding=item["embedding"]
                )
                session.add(new_laptop)
                count += 1

        session.commit()

    print(f"[SUCCESS] Added {count} new laptops to your database.")
    print(f"   (Skipped {len(data) - count} that already existed)")


if __name__ == "__main__":
    data = scrape_all_pages()
    save_to_db(data)