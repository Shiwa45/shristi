import os
import time
import argparse
import pandas as pd
import itertools
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.common.exceptions import StaleElementReferenceException
import json

# Configuration
DEFAULT_OUTPUT_FILE = "kraftix_pricing.xlsx"

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

def setup_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Add a real user agent to avoid detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

class KraftixScraper:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    def get_xpath_from_selector(self, css_selector):
         # Very basic converter for the specific selector we use
         if "button[data-toggle='dropdown']" in css_selector:
             return "//button[@data-toggle='dropdown'] | //div[contains(@class, 'dropdown')]/button"
         return "//*[contains(@class, 'dropdown')]" # Fallback

    def get_options(self):
        """
        Identify all interactive options on the product page.
        Returns a dictionary where keys are option names (e.g., 'Size', 'Quantity')
        and values are lists of (value_name, web_element) tuples.
        """
        options_map = {}
        
        # 1. Look for Select dropdowns
        selects = self.driver.find_elements(By.CSS_SELECTOR, "select.form-control") # Adjust selector based on inspection
        # Also check for hidden selects that might be driven by other UI elements
        all_selects = self.driver.find_elements(By.TAG_NAME, "select")
        
        for select in all_selects:
            try:
                # Filter out irrelevant selects
                if not select.is_displayed():
                    # Some sites hide the actual select and show a custom UI. 
                    # We might need to interact with the custom UI or the hidden select directly if possible.
                    # For now, let's focus on visible ones or those that look like product options
                    pass

                # Get the label for this select
                # Heuristic: Find the preceding label or the name attribute
                label_text = "Unknown Option"
                parent = select.find_element(By.XPATH, "./..")
                # Try to find a previous sibling that is a label or strong tag
                try:
                    # XPath to find preceding label
                    label_elem = select.find_element(By.XPATH, "preceding-sibling::label")
                    label_text = label_elem.text.strip()
                except:
                    # Try getting it from the name or id
                    label_text = select.get_attribute("name") or select.get_attribute("id")

                # Parse options
                select_obj = Select(select)
                option_values = []
                for opt in select_obj.options:
                    txt = opt.text.strip()
                    val = opt.get_attribute("value")
                    if txt and val and "select" not in txt.lower(): # Skip "Select Size" etc.
                        option_values.append({'type': 'select', 'text': txt, 'value': val, 'element': select})
                
                if option_values:
                    options_map[label_text] = option_values
            except Exception as e:
                print(f"Error parsing select: {e}")

        # 2. Look for Button-based options (like Size/Qty often are on modern sites)
        # Based on inspection: <button title="3" ...>
        # And <div class="materials-options">...</div>
        
        # ... (We will implement dynamic detection below based on successful manual inspection patterns)
        
        return options_map

    def select_option_with_retry(self, option, max_retries=3):
        for attempt in range(max_retries):
            try:
                if option['type'] == 'select':
                    if 'locator' in option:
                        sel_elem = self.driver.find_element(*option['locator'])
                    else:
                        sel_elem = option['element']
                    Select(sel_elem).select_by_value(option['value'])

                elif option['type'] == 'click':
                    elem = option['element']
                    if 'locator' in option:
                        elem = self.driver.find_element(*option['locator'])
                    elem.click()

                elif option['type'] == 'custom_dropdown':
                    btn = option['button_element']
                    if 'locator' in option:
                        btn = self.driver.find_element(*option['locator'])
                    
                    # Open
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.5)

                    # Select
                    xpath = f"//div[contains(@class,'dropdown-menu') and contains(@class,'show')]//span[contains(text(), \"{option['option_text']}\")]"
                    visible_opts = self.driver.find_elements(By.XPATH, xpath)
                    if not visible_opts:
                         xpath_alt = f"//div[contains(@class,'dropdown-menu') and contains(@class,'show')]//li[contains(., \"{option['option_text']}\")]"
                         visible_opts = self.driver.find_elements(By.XPATH, xpath_alt)
                    
                    if visible_opts:
                        self.driver.execute_script("arguments[0].click();", visible_opts[0])
                    else:
                        # Close if not found to reset state
                        self.driver.execute_script("arguments[0].click();", btn)
                        raise Exception(f"Option '{option['option_text']}' not visible in dropdown")

                return # Success
            except (StaleElementReferenceException, Exception) as e:
                # Only retry on StaleElement or general transient issues if checked
                if attempt == max_retries - 1:
                    raise e
                time.sleep(1)


    def scrape_product(self, url, test_mode=False):
        print(f"Navigating to {url}...")
        self.driver.get(url)
        time.sleep(3) # Wait for load

        product_name = self.driver.find_element(By.TAG_NAME, "h1").text.strip()
        print(f"Scraping Product: {product_name}")

        # --- Dynamic Option Discovery ---
        # Based on the inspection:
        # Size/Qty are buttons that open dropdowns, OR standard selects.
        # Materials are often radio-like divs.
        
        option_groups = {} # { 'Size': [opt1, opt2], 'Quantity': [100, 200] }

        # Strategy 1: Find all valid 'SELECT' elements (simplest form)
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        for sel in selects:
            # Check visibility or if it's a product option
            # Kraftix uses Selects for many options based on 'inspect_kraftix_options' logs (select#aoptions[470])
            try:
                if 'aoptions' in sel.get_attribute('id') or 'option' in sel.get_attribute('name'):
                    # It's likely a product option
                    label = "Option " + sel.get_attribute('id') # specific label finding is tricky, keying by ID is safer for uniqueness
                    
                    # Try to find a human readable label
                    # Strategy 1: Check for <label for="element_id"> (Robust)
                    try:
                        element_id = sel.get_attribute("id")
                        if element_id:
                            label_elem = self.driver.find_element(By.XPATH, f"//label[@for='{element_id}']")
                            # Check visibility not strictly required if the select is what we are targeting, 
                            # but helps ensure it's the right label
                            if label_elem.is_displayed() or label_elem.get_attribute("class"): 
                                txt = label_elem.text.strip()
                                if txt:
                                    label = txt
                    except:
                        pass
                    
                    if "Option" in label and "aoptions" in label:
                        # Fallback try: Preceding sibling
                         try:
                            parent = sel.find_element(By.XPATH, "..")
                            # Look for label inside the parent col or row
                            ancestor = sel.find_element(By.XPATH, "./ancestor::div[contains(@class, 'form-group') or contains(@class, 'row')]")
                            found_labels = ancestor.find_elements(By.TAG_NAME, "label")
                            if found_labels:
                                label = found_labels[0].text.strip()
                         except:
                            pass

                    opts = []
                    select_obj = Select(sel)
                    for opt in select_obj.options:
                        txt = opt.text.strip()
                        if txt and "select" not in txt.lower():
                            opts.append({
                                'type': 'select', 
                                'name': txt, 
                                'element': sel, 
                                'locator': (By.ID, sel.get_attribute('id')), 
                                'value': opt.get_attribute('value') 
                            })
                    if opts:
                         # CLEANUP: Deduplicate by content here too
                         is_duplicate = False
                         current_opts_sig = sorted([o['name'].strip() for o in opts])
                         
                         for existing_label, existing_opts in option_groups.items():
                             existing_opts_sig = sorted([o['name'].strip() for o in existing_opts])
                             if current_opts_sig == existing_opts_sig:
                                 is_duplicate = True
                                 break
                        
                         if not is_duplicate:
                            # Use valid keys for checking
                            original_label = label
                            counter = 1
                            while label in option_groups:
                                label = f"{original_label} {counter}"
                                counter += 1
                            option_groups[label] = opts
            except:
                continue
        
        # Strategy 2: Find "Material" radio-like options (from inspection: label.custom-control-label containing div[role='button'])
        material_labels = self.driver.find_elements(By.CSS_SELECTOR, "label.custom-control-label")
        material_opts = []
        for lbl in material_labels:
            try:
                btn = lbl.find_element(By.CSS_SELECTOR, "div[role='button']")
                name = btn.text.strip()
                if name:
                    material_opts.append({
                        'type': 'click',
                        'name': name,
                        'element': lbl,
                        'locator': (By.XPATH, f"//label[contains(@class, 'custom-control-label')]//div[@role='button' and contains(text(), '{name}')]/../..") # Heuristic Xpath
                    })
            except:
                pass
        
        if material_opts:
            option_groups['Material'] = material_opts

        # Strategy 3: Bootstrap/Custom Dropdowns (Buttons that open lists)
        # Look for buttons that might be dropdown toggles.
        # Heuristic: Buttons inside a form-group or similar context, often having a title attribute.
        dropdown_selector = "button[data-toggle='dropdown'], div.dropdown > button"
        dropdown_buttons = self.driver.find_elements(By.CSS_SELECTOR, dropdown_selector)
        
        for idx, btn in enumerate(dropdown_buttons):
            try:
                # Get label from parent/sibling
                label = "Unknown Dropdown"
                
                # Strategy 1: Check for <label for="element_id">
                # This is the most robust method
                try:
                    element_id = btn.get_attribute("id")
                    if element_id:
                        # Find label with for="element_id"
                        label_elem = self.driver.find_element(By.XPATH, f"//label[@for='{element_id}']")
                        if label_elem.is_displayed():
                            label = label_elem.text.strip()
                            # print(f"Found label by ID match: {label}")
                except:
                    pass

                # Strategy 2: Find closely associated label text if ID match failed
                if label == "Unknown Dropdown":
                    try:
                        # Traversal: Limit scope! 
                        # Only go up 3 levels max to avoid finding labels of previous groups
                        # btn -> div(dropdown) -> col -> form-group
                        ancestor = btn.find_element(By.XPATH, "./..") # dropdown div
                        found = False
                        for _ in range(3):
                            # Check siblings for label
                            try:
                                sib_label = ancestor.find_elements(By.XPATH, "preceding-sibling::label") or \
                                            ancestor.find_elements(By.XPATH, ".//label")
                                if sib_label:
                                     label = sib_label[0].text.strip()
                                     found = True
                                     break
                            except: pass
                            
                            # Check cols inside this ancestor
                            cols = ancestor.find_elements(By.XPATH, "./div[contains(@class, 'col-')]")
                            for col in cols:
                                 if not col.find_elements(By.TAG_NAME, "button"):
                                      txt = col.text.strip()
                                      if txt:
                                           label = txt
                                           found = True
                                           break
                            if found: break
                            
                            # Go up one level
                            try:
                                ancestor = ancestor.find_element(By.XPATH, "./..")
                            except:
                                break
                    except Exception as e:
                        pass
                
                # Validation: If label is empty strings or "Quantity" is misspelled?
                if not label:
                    label = "Unknown Dropdown"
                
                # Fallback: Check 'title' attribute of the button itself if it contains hint? 
                # (Inspection showed title="40mm Dia", which is the value, not the label)
                
                # Check uniqueness and deduplicate
                
                # CLEANUP: Deduplicate by content! 
                # If we already have a field with EXACTLY the same options, skip this one.
                # (Handles hidden duplicate fields for mobile/desktop)
                # This check needs to happen AFTER options are extracted, so it's moved below.

                # Check uniqueness and deduplicate
                original_label = label
                counter = 1
                while label in option_groups: 
                    label = f"{original_label} {counter}"
                    counter += 1

                # Open the dropdown to see options
                if not btn.is_displayed(): continue
                
                # Scroll to it
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                # Use JS Click to avoid interception
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
                
                # Find the appearing menu
                # Usually it's a sibling or child 'dropdown-menu'
                # We can look for the visible dropdown-menu in the document
                visible_menus = self.driver.find_elements(By.CSS_SELECTOR, "div.dropdown-menu.show")
                
                opts = []
                if visible_menus:
                    menu = visible_menus[-1] # usage assumption: last opened is the one
                    # Extract clickable items
                    items = menu.find_elements(By.TAG_NAME, "li") or menu.find_elements(By.TAG_NAME, "a") or menu.find_elements(By.CSS_SELECTOR, "span.text")
                    
                    seen_values = set()
                    for item in items:
                        txt = item.text.strip()
                        if txt and txt not in seen_values:
                            seen_values.add(txt)
                            # Logic to select this option:
                            # We need to click the specific element that triggers the selection.
                            # Often it's the <li> or <a> itself.
                            opts.append({
                                'type': 'custom_dropdown',
                                'name': txt,
                                'button_element': btn,
                                # Store distinct locator using the index directly
                                # This assumes the order of dropdowns on page is static (which is typical for product pages)
                                'locator': (By.XPATH, f"({self.get_xpath_from_selector(dropdown_selector)})[{idx+1}]"),
                                'option_text': txt
                            })
                    
                    # Close dropdown
                    try:
                         self.driver.execute_script("arguments[0].click();", btn)
                    except:
                        pass
                
                if opts:
                     # Heuristic: Detect Quantity field by numeric values (e.g. 50, 100, 200)
                     # If the label is "Unknown" or looks like a duplicate "Closed Size 1"
                     first_opts = [o['name'] for o in opts[:5]]
                     if len(first_opts) > 2 and all(x.isdigit() for x in first_opts):
                         label = "Quantity"

                     # CLEANUP: Deduplicate by content
                     # Check if we already have a field with these EXACT options
                     is_duplicate = False
                     current_opts_sig = sorted([o['name'] for o in opts])
                     
                     for existing_label, existing_opts in option_groups.items():
                         existing_opts_sig = sorted([o['name'] for o in existing_opts])
                         if current_opts_sig == existing_opts_sig:
                             # print(f"Skipping duplicate field (matches {existing_label})")
                             is_duplicate = True
                             break
                     
                     if not is_duplicate:
                         # Ensure unique label key
                         original_label = label
                         counter = 1
                         while label in option_groups:
                             label = f"{original_label} {counter}"
                             counter += 1
                         
                         option_groups[label] = opts
                     
            except Exception as e:
                print(f"Error processing dropdown button: {e}")

        # Print found options
        print(f"Found {len(option_groups)} option groups:")
        for k, v in option_groups.items():
            print(f"  - {k}: {len(v)} choices ({', '.join([x['name'] for x in v[:3]])}...)")

        if not option_groups:
            print("No options found. Scraping single price.")
            # TODO: Handle no-option products
            return []

        # Refactored: Linear Option Extraction (No Combinations)
        print(f"Found {len(option_groups)} option groups.")

        # Scrape Base Price once
        base_price = "N/A"
        try:
             # Strategy 1: Specific Selectors
            try:
                price_box = self.driver.find_element(By.CSS_SELECTOR, "div.pricing-details")
                base_price = price_box.text.split('\n')[0]
            except:
                # Strategy 2: Common Price Classes
                try:
                    price_box = self.driver.find_element(By.CSS_SELECTOR, ".price, .special-price, .regular-price, #price-box")
                    base_price = price_box.text.strip()
                except:
                     pass
        except:
            pass

        results = []
        
        # JSON Structure Construction
        json_entry = {
            "title": product_name,
            "base_price": base_price,
            "fields": []
        }
        
        # Iterate through each group and list its options
        for group_name, options in option_groups.items():
            field_data = {
                "name": group_name,
                "options": [opt['name'] for opt in options]
            }
            json_entry["fields"].append(field_data)
            
            # Add to flat list for Excel as well
            for opt in options:
                results.append({
                    'Product': product_name,
                    'Base Price': base_price,
                    'Field Name': group_name,
                    'Field Option': opt['name']
                })

        print(f"Extracted {len(results)} option rows.")
        return results, json_entry

    def crawl_all_products(self):
        """
        Navigate to homepage and extract all product URLs from the specific dropdown classes.
        """
        print("Navigating to homepage for crawling...")
        self.driver.get("https://www.kraftixdigital.in/")
        time.sleep(5)
        
        # DEBUG: Save source to check for links
        with open("debug_crawl_source.html", "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

        product_urls = set()
        
        # Selectors identified in analysis
        # - a.edatalayer.dropdown-item
        # - a.all-product.dropdown-item
        
        # We need to hover/click to ensure they are loaded in DOM if lazy loaded?
        # Usually they are present but hidden. Let's try finding them directly first.
        try:
            # Look for all links that match the product classes
            links = self.driver.find_elements(By.CSS_SELECTOR, "a.edatalayer.dropdown-item, a.all-product.dropdown-item")
            print(f"Found {len(links)} potential product links.")
            
            for link in links:
                href = link.get_attribute("href")
                if href and "javascript" not in href and "tel:" not in href and "mailto:" not in href:
                     # Basic deduplication and validation
                    if "kraftixdigital.in" in href or href.startswith("/"):
                     text = link.get_attribute("textContent").strip()
                     # DRAGNET MODE: Scrape EVERYTHING. Filter later in DB script.
                     # This ensures we catch variants like "Envelopes A-4" which might have weird names.
                     if text:
                        product_urls.add(href)
                     
                     # Original Filter Logic (Disabled)
                     # is_target = False
                     # for target in TARGET_PRODUCTS:
                     #     if target.lower() in text.lower() or text.lower() in target.lower():
                     #         is_target = True
                     #         break
                     # if is_target:
                     #     product_urls.add(href)
                         # else:
                         #    print(f"Skipping non-target product: {text}")

             # Also try finding links inside standard dropdowns if the above misses some
             # (Fallback or supplementary logic could go here)
            
        except Exception as e:
            print(f"Error extracting product links: {e}")
            
        sorted_urls = sorted(list(product_urls))
        print(f"Discovered {len(sorted_urls)} unique product URLs matching target list.")
        print("--- URL Queue ---")
        for u in sorted_urls:
            print(f"Queue: {u}")
        print("-----------------")
        return sorted_urls

def main():
    parser = argparse.ArgumentParser(description="Kraftix Pricing Scraper")
    parser.add_argument("--url", help="Specific product URL to scrape", required=False)
    parser.add_argument("--crawl", action="store_true", help="Crawl site for all products")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FILE, help="Output Excel file")
    parser.add_argument("--test", action="store_true", help="Run in test mode (fewer products/combinations)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode") 
    
    args = parser.parse_args()

    driver = setup_driver(headless=args.headless)
    scraper = KraftixScraper(driver)
    
    all_data = []
    json_data_list = []

    try:
        urls_to_scrape = []
        if args.url:
            urls_to_scrape = [args.url]
        elif args.crawl:
            urls_to_scrape = scraper.crawl_all_products()
            if args.test:
                print("TEST MODE: Limiting to first 3 products.")
                urls_to_scrape = urls_to_scrape[:3]
        else:
            print("Please provide --url or --crawl")
            return

        for i, url in enumerate(urls_to_scrape):
            print(f"\n--- Processing Product {i+1}/{len(urls_to_scrape)} ---")
            try:
                # scraper.scrape_product now returns tuple (rows, json_obj)
                res = scraper.scrape_product(url, test_mode=args.test)
                
                # Handle return type flexibility just in case
                if isinstance(res, tuple):
                    rows, json_obj = res
                    all_data.extend(rows)
                    if json_obj:
                        json_data_list.append(json_obj)
                else:
                    all_data.extend(res) # Fallback
                
                # Checkpoint save (optional but good for long runs)
                if all_data:
                    df = pd.DataFrame(all_data)
                    df.to_excel(args.output, index=False)
                    print(f"Progress saved to {args.output}")
                    
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")
                continue

    except Exception as e:
        print(f"Fatal Error: {e}")
    finally:
        driver.quit()
        
        if all_data:
            df = pd.DataFrame(all_data)
            df.to_excel(args.output, index=False)
            print(f"\nFinal Excel data saved to {args.output}")
            
        if json_data_list:
            json_file = "kraftix_products.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data_list, f, indent=4, ensure_ascii=False)
            print(f"Final JSON data saved to {json_file}")
        else:
            print("No data collected.")

if __name__ == "__main__":
    main()
