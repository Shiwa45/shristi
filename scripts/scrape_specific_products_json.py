import os
import sys
import time
import json
from django.utils.text import slugify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from webdriver_manager.chrome import ChromeDriverManager

TARGET_PRODUCTS = [
    'Address Labels', 'Banner Media', 'Barcode Labels', 'Bi-fold Brochure', 
    'Black & White Bill Book', 'Button Badges', 'Certificates', 'Circle Stickers', 
    'Colour Bill Book', 'Corporate Letter Head', 'Custom Paper Boxes', 
    'Custom Stickers', 'Document Printing', 'Envelopes 10x 4.5', 
    'Envelopes A-3', 'Envelopes A-4', 'Envelopes A-5', 'Envelopes A-6', 'Event ID Cards', 'Hang Tags', 
    'Kraft Paper Product Box', 'Multicolour Lanyards', 'PVC ID Cards', 'Paper Bag', 
    'Premium Flex', 'Product Labels', 'Rectangle Stickers', 
    'Square Stickers', 'Standard Business Card', 'Standard Letter Head', 'TEXTURE BUSINESS CARD', 
    'Tent Card', 'Tri-fold Brochure', 'Warning Labels'
]

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
                if not sel.is_displayed():
                    if 'option' not in sel.get_attribute('id') and 'option' not in sel.get_attribute('name'):
                        continue

                label = "Option"
                try:
                    eid = sel.get_attribute("id")
                    if eid:
                        l = self.driver.find_element(By.XPATH, f"//label[@for='{eid}']")
                        label = l.text.strip()
                except:
                    pass
                
                if label == "Option":
                     try:
                        parent = sel.find_element(By.XPATH, "..")
                        label = parent.find_element(By.TAG_NAME, "strong").text.strip()
                     except:
                        pass

                opts = []
                for o in Select(sel).options:
                    txt = o.text.strip()
                    if txt and "select" not in txt.lower():
                        opts.append(txt)
                
                if opts:
                    base_label = label
                    cnt = 1
                    while label in options_map:
                        label = f"{base_label} {cnt}"
                        cnt += 1
                    options_map[label] = opts
            except:
                pass

        # 2. Custom Dropdowns
        buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[data-toggle='dropdown']")
        for btn in buttons:
            try:
                if not btn.is_displayed(): continue
                
                label = "Unknown"
                try:
                    ancestor = btn.find_element(By.XPATH, "./ancestor::div[contains(@class, 'col')]")
                    label = ancestor.find_element(By.TAG_NAME, "label").text.strip()
                except:
                    pass

                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
                
                menu = self.driver.find_element(By.CSS_SELECTOR, "div.dropdown-menu.show")
                items = menu.find_elements(By.TAG_NAME, "a") + menu.find_elements(By.TAG_NAME, "li")
                
                opts = []
                seen = set()
                for item in items:
                    txt = item.text.strip()
                    if txt and txt not in seen:
                        seen.add(txt)
                        opts.append(txt)
                
                self.driver.execute_script("arguments[0].click();", btn)
                
                if opts:
                    if len(opts) > 2 and all(o.replace(',','').isdigit() for o in opts[:3]):
                        label = "Quantity"
                    
                    base_label = label
                    cnt = 1
                    while label in options_map:
                        label = f"{base_label} {cnt}"
                        cnt += 1
                        
                    options_map[label] = opts
            except:
                pass

        return options_map

    def scrape(self):
        print("Scraping started...")
        self.driver.get("https://www.kraftixdigital.in/")
        time.sleep(3)
        
        # Collect all product links
        links = self.driver.find_elements(By.CSS_SELECTOR, "a.dropdown-item")
        potential_urls = {}
        for link in links:
            href = link.get_attribute("href")
            text = link.get_attribute("textContent").strip()
            if href and text:
                potential_urls[href] = text
        
        print(f"Found {len(potential_urls)} links on homepage.")
        
        results = {}
        
        for target in TARGET_PRODUCTS:
            print(f"\nSearching for: {target}")
            # Find best matching URL
            best_url = None
            
            # 1. Try exact text match
            for url, text in potential_urls.items():
                if normalize(target) == normalize(text):
                    best_url = url
                    break
            
            # 2. Try contains match if explicit fail
            if not best_url:
                for url, text in potential_urls.items():
                    if normalize(target) in normalize(text) or normalize(text) in normalize(target):
                        best_url = url
                        break
            
            if not best_url:
                print(f" - No URL found for {target}")
                continue
                
            print(f" - Found URL: {best_url}")
            try:
                self.driver.get(best_url)
                time.sleep(2)
                
                fields = self.get_options()
                if fields:
                    results[target] = fields
                    print(f"   -> Scraped {len(fields)} fields.")
                else:
                    print("   -> No fields found.")
                    
            except Exception as e:
                print(f"   -> Error: {e}")

        # Save to JSON
        output_file = "product_fields.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
            
        print(f"\nSAVED JSON to {output_file}")


def main():
    driver = setup_driver()
    try:
        scraper = FieldScraper(driver)
        scraper.scrape()
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
