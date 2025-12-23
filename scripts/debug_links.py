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

def main():
    driver = setup_driver()
    try:
        print("Visiting Homepage...")
        driver.get("https://www.kraftixdigital.in/")
        time.sleep(5)
        
        # Broad search for ALL links
        links = driver.find_elements(By.TAG_NAME, "a")
        print(f"Found {len(links)} links with broad selector.")
        
        print("\n--- Links Found ---")
        for link in links:
            try:
                text = link.get_attribute("textContent").strip()
                href = link.get_attribute("href")
                print(f"Text: '{text}' | Href: {href}")
            except:
                pass
                
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
