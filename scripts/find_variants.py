from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

CATEGORIES = [
    "https://www.kraftixdigital.in/envelopes/products/",
    "https://www.kraftixdigital.in/bill-book/products/",
    "https://www.kraftixdigital.in/id-cards/products/",
    "https://www.kraftixdigital.in/stickers-labels/products/",
    "https://www.kraftixdigital.in/stationery/products/",
    "https://www.kraftixdigital.in/marketing/products/",
    "https://www.kraftixdigital.in/packaging/products/",
    "https://www.kraftixdigital.in/en/stickers-by-shape/products/",
    "https://www.kraftixdigital.in/en/stickers-by-material/products/",
    # Add generic 'products' listing if possible
    "https://www.kraftixdigital.in/all-products/", 
]

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def main():
    driver = setup_driver()
    try:
        for cat_url in CATEGORIES:
            print(f"\nScanning Category: {cat_url}")
            try:
                driver.get(cat_url)
                time.sleep(5)
                
                # Get all links
                links = driver.find_elements(By.TAG_NAME, "a")
                print(f"Found {len(links)} links.")
                
                for link in links:
                    try:
                        text = link.text.strip()
                        href = link.get_attribute("href")
                        if href and "kraftixdigital.in" in href and len(text) > 3:
                            # Filter mostly valid product names
                            print(f"  LINK: {text} -> {href}")
                    except:
                        pass
            except Exception as e:
                print(f"Failed to load {cat_url}: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
