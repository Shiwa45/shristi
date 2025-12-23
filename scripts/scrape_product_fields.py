import os
import sys
import django
import time
import json
from django.utils.text import slugify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from webdriver_manager.chrome import ChromeDriverManager

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')
django.setup()

from apps.services.models import StaticProduct, ProductFormField, ServiceCategory

# Helper to normalize names for matching
def normalize(name):
    return name.lower().strip().replace("  ", " ")

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

class FieldScraper:
    def __init__(self, driver):
        self.driver = driver
        
    def get_options(self):
        """Extract all interactive options"""
        options_map = {}
        
        # 1. Standard Selects
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        for sel in selects:
            try:
                # Basic visibility check
                if not sel.is_displayed():
                    # Check if it has a specific ID indicating it's a product option
                    if 'option' not in sel.get_attribute('id') and 'option' not in sel.get_attribute('name'):
                        continue

                label = "Option"
                # Try finding label
                try:
                    eid = sel.get_attribute("id")
                    if eid:
                        l = self.driver.find_element(By.XPATH, f"//label[@for='{eid}']")
                        label = l.text.strip()
                except:
                    pass
                
                # Check for "Material" or generic labels if not found
                if label == "Option":
                     # Look at preceding siblings or parent containers
                     try:
                        parent = sel.find_element(By.XPATH, "..")
                        label = parent.find_element(By.TAG_NAME, "strong").text.strip()
                     except:
                        pass

                # Get options
                opts = []
                for o in Select(sel).options:
                    txt = o.text.strip()
                    val = o.get_attribute("value")
                    if txt and "select" not in txt.lower():
                        opts.append({'value': val, 'label': txt, 'price_modifier': 0})
                
                if opts:
                    # Deduplicate key
                    base_label = label
                    cnt = 1
                    while label in options_map:
                        label = f"{base_label} {cnt}"
                        cnt += 1
                        
                    options_map[label] = {
                        'type': 'select',
                        'options': opts
                    }
            except Exception as e:
                # print(f"Select error: {e}")
                pass

        # 2. Custom Dropdowns (Bootstrap)
        # Often used for Quantity or Material
        buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[data-toggle='dropdown']")
        for btn in buttons:
            try:
                if not btn.is_displayed(): continue
                
                # Try to guess label from context
                label = "Unknown"
                try:
                    # Look for preceding label in the same column/row
                    ancestor = btn.find_element(By.XPATH, "./ancestor::div[contains(@class, 'col')]")
                    label = ancestor.find_element(By.TAG_NAME, "label").text.strip()
                except:
                    pass

                # Open it
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
                
                # Find the menu
                menu = self.driver.find_element(By.CSS_SELECTOR, "div.dropdown-menu.show")
                items = menu.find_elements(By.TAG_NAME, "a") + menu.find_elements(By.TAG_NAME, "li")
                
                opts = []
                seen = set()
                for item in items:
                    txt = item.text.strip()
                    if txt and txt not in seen:
                        seen.add(txt)
                        opts.append({'value': txt, 'label': txt, 'price_modifier': 0})
                
                # Close it
                self.driver.execute_script("arguments[0].click();", btn)
                
                if opts:
                    # Heuristic: if options are numbers, it's Quantity
                    if len(opts) > 2 and all(o['label'].replace(',','').isdigit() for o in opts[:3]):
                        label = "Quantity"
                    
                    base_label = label
                    cnt = 1
                    while label in options_map:
                        label = f"{base_label} {cnt}"
                        cnt += 1
                        
                    options_map[label] = {
                        'type': 'select', # Treat as select for our DB
                        'options': opts
                    }
            except:
                pass

        return options_map

    def crawl_and_update(self):
        print("Navigating to homepage...")
        self.driver.get("https://www.kraftixdigital.in/")
        time.sleep(3)
        
        # Collect all product links
        links = self.driver.find_elements(By.CSS_SELECTOR, "a.dropdown-item")
        product_urls = set()
        for link in links:
            href = link.get_attribute("href")
            if href and "javascript" not in href and ("product" in href or "kraftixdigital.in/" in href):
                 if "/category/" not in href: # Try to avoid category pages if possible
                    product_urls.add(href)
        
        print(f"Found {len(product_urls)} potential product URLs.")
        
        # Get our DB products
        db_products = list(StaticProduct.objects.filter(is_active=True))
        print(f"We have {len(db_products)} active products in DB.")
        
        matched_urls = []
        for url in product_urls:
            # We don't verify name match yet, we have to visit OR guess from URL
            # Urls are like /product-name
            slug_part = url.strip('/').split('/')[-1].replace('-', ' ').lower()
            
            # Try to match with DB product names
            for p in db_products:
                if normalize(p.name) in normalize(slug_part) or normalize(slug_part) in normalize(p.name):
                    matched_urls.append((url, p))
                    break
        
        print(f"Matched {len(matched_urls)} URLs to our products.")
        
        # Process Matches
        for url, product in matched_urls:
            print(f"\n--- Processing {product.name} ({url}) ---")
            try:
                self.driver.get(url)
                time.sleep(2)
                
                # Check for 404
                if "404" in self.driver.title:
                    print("Page not found, skipping.")
                    continue

                fields_map = self.get_options()
                
                if not fields_map:
                    print("No fields found on page.")
                    continue
                
                # UPDATE DB
                # Clear existing
                ProductFormField.objects.filter(static_product=product).delete()
                
                order_cnt = 1
                for label, data in fields_map.items():
                    # Map loop to DB types
                    ftype = 'number' if label == 'Quantity' else 'select'
                    fsection = 'quantity_pricing' if label == 'Quantity' else 'product_specs'
                    
                    # Normalize Label
                    clean_label = label.replace("Select", "").strip()
                    if not clean_label: clean_label = "Options"
                    
                    # Store options
                    # If quantity, we might just want to store it as a number input or select
                    # User likely wants the dropdowns if available
                    
                    ProductFormField.objects.create(
                        static_product=product,
                        field_name=slugify(clean_label).replace('-', '_'),
                        field_label=clean_label,
                        field_type=ftype,
                        field_section=fsection,
                        order=order_cnt,
                        is_required=True,
                        is_price_affecting=True, # Assume yes
                        options=json.dumps(data['options'])
                    )
                    print(f"  + Added Field: {clean_label} ({len(data['options'])} opts)")
                    order_cnt += 1
                    
            except Exception as e:
                print(f"Error scraping {product.name}: {e}")

def main():
    driver = setup_driver()
    try:
        scraper = FieldScraper(driver)
        scraper.crawl_and_update()
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
