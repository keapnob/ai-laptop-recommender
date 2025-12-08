import time
from playwright.sync_api import sync_playwright

def investigate_notebookspec():
    print("🕵️ Starting Detective Script for NotebookSpec...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # 1. Go to the page
        url = "https://notebookspec.com/notebook/search"
        print(f"🌍 Navigating to {url}...")
        page.goto(url)
        
        # 2. Wait blindly for 10 seconds (to let ads/popups finish)
        print("⏳ Waiting 10 seconds for page to settle...")
        page.wait_for_timeout(10000)

        # 3. Take a Screenshot (CRITICAL)
        # If this image shows a "Verify Human" or "Access Denied", we are blocked.
        page.screenshot(path="debug_nbs.png")
        print("📸 Screenshot saved to 'debug_nbs.png'. PLEASE CHECK THIS IMAGE.")

        # 4. Try to find the data by searching for the Price Symbol "฿"
        # This is a "Smart Search" - it ignores class names and looks for money.
        print("🔍 Scanning for prices (฿)...")
        price_elements = page.locator("text=฿").all()
        
        if len(price_elements) > 0:
            print(f"✅ Found {len(price_elements)} price tags!")
            
            # Get the first one and look at its parent to find the "Product Box"
            first_price = price_elements[0]
            parent = first_price.locator("..").locator("..") # Go up 2 levels
            
            try:
                class_name = parent.get_attribute("class")
                html_sample = parent.inner_html()[:200] # First 200 chars
                print(f"\n💡 CLUE FOUND:")
                print(f"   The Laptop Card seems to have class: '{class_name}'")
                print(f"   HTML Sample: {html_sample}...\n")
            except:
                print("   (Could not read parent class)")
        else:
            print("❌ Could not find any '฿' symbol. The page might be empty or blocked.")

        # 5. Check Page Title
        print(f"📄 Page Title is: '{page.title()}'")

        browser.close()

if __name__ == "__main__":
    investigate_notebookspec()