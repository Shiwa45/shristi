import requests
import time
from bs4 import BeautifulSoup
import urllib.parse

# Endpoint identified from page source
SEARCH_URL = "https://www.kraftixdigital.in/search/"
# Or the advance search:
ADVANCE_SEARCH_URL = "https://www.kraftixdigital.in/advance_search.php"

MISSING_PRODUCTS = [
    'Banner Media', 'Barcode Labels', 'Black & White Bill Book', 'Circle Stickers', 
    'Classic Shape', 'Colour Bill Book', 'Custom Size', 'Custom Stickers', 
    'Custom/Any Other Shape', 'Document Printing', 'Envelopes 10x 4.5', 'Envelopes A-3', 
    'Envelopes A-4', 'Envelopes A-5', 'Envelopes A-6', 'Event ID Cards', 'Multicolour Lanyards', 
    'Normal Shape', 'PVC ID Cards', 'Premium Flex', 'Round Shape', 'Size A-3', 'Size A-4', 
    'Square Stickers'
]

def search_product(query):
    # Try simple GET with keywords
    params = {
        'search_section': 'products',
        'keywords': query,
        'search': 'Search' # Common submit button name
    }
    
    # Try constructing the search URL commonly used: /search?q=...
    # But based on grep, it's likely a POST or GET to advance_search.php
    
    try:
        # User agent is critical
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        # Try method 1: GET advance_search
        url = f"{ADVANCE_SEARCH_URL}?search_section=products&term={urllib.parse.quote(query)}"
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            # Parse HTML
            soup = BeautifulSoup(r.text, 'html.parser')
            # Look for any links in results
            links = soup.find_all('a')
            found = []
            for a in links:
                href = a.get('href')
                text = a.get_text().strip()
                if href and 'kraftixdigital.in' in href and 'advance_search' not in href:
                     found.append((text, href))
                elif href and not href.startswith('#') and 'advance_search' not in href and not href.startswith('javascript'):
                     found.append((text, href))
            
            return found
            
    except Exception as e:
        print(f"Error searching {query}: {e}")
        return []
    
    return []

def main():
    print("Searching for missing products...")
    
    for product in MISSING_PRODUCTS:
        # Simplify query: "Envelopes A-4" -> "Envelopes" to get more results
        # Or try exact match first
        
        print(f"\n--- Searching for: {product} ---")
        results = search_product(product)
        if not results:
            # Retry with first word
            first_word = product.split()[0]
            print(f"  Retrying with '{first_word}'...")
            results = search_product(first_word)
            
        seen = set()
        for text, href in results:
            # Filter garbage
            if href in seen: continue
            seen.add(href)
            
            # Simple validity check
            if len(href) > 20: 
                print(f"  FOUND: {text[:30]}... -> {href}")

if __name__ == "__main__":
    main()
