from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

TARGETS = [
    'Banner Media', 'Barcode Labels', 'Black & White Bill Book', 'Circle Stickers', 
    'Classic Shape', 'Colour', 'Colour Bill Book', 'Custom Size', 'Custom Stickers', 
    'Custom/Any Other Shape', 'Document Printing', 'Envelopes 10x 4.5', 'Envelopes A-3', 
    'Envelopes A-4', 'Envelopes A-5', 'Envelopes A-6', 'Event ID Cards', 'Multicolour Lanyards', 
    'Normal Shape', 'PVC ID Cards', 'Premium Flex', 'Round Shape', 'Size A-3', 'Size A-4', 
    'Square Stickers'
]

def main():
    driver = setup_driver()
    try:
        print("Visiting Homepage...")
        driver.get("https://www.kraftixdigital.in/")
        time.sleep(5)
        
        links = driver.find_elements(By.TAG_NAME, "a")
        print(f"Found {len(links)} links.")
        
        found_map = {}
        
        for link in links:
            try:
                href = link.get_attribute("href")
                text = link.text.strip()
                if not href or not text:
                    continue
                
                # Check against targets
                for t in TARGETS:
                    # Logic: If target words are in link text OR target words are in href (slugified)
                    t_slug = t.lower().replace(" ", "-")
                    text_lower = text.lower()
                    
                    match = False
                    if t.lower() in text_lower:
                        match = True
                    elif t_slug in href:
                        match = True
                    
                    if match:
                        if t not in found_map:
                            found_map[t] = []
                        if href not in found_map[t]:
                            found_map[t].append(href)
                            print(f"MATCH: '{t}' -> {href} (Text: {text})")
            except:
                continue

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
