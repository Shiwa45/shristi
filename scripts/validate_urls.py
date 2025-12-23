import requests
import time

BASE_URL = "https://www.kraftixdigital.in/"

# Map of Product Name -> List of Guesses
GUESSES = {
    'Black & White Bill Book': ['black-white-bill-book', 'bill-book-black-white', 'bill-book', 'bill-books'],
    'Colour Bill Book': ['colour-bill-book', 'bill-book-colour', 'color-bill-book'],
    'Envelopes A-3': ['envelopes-a3', 'a3-envelopes', 'envelope-a3'],
    'Envelopes A-4': ['envelopes-a4', 'a4-envelopes', 'envelope-a4'],
    'Envelopes A-5': ['envelopes-a5', 'a5-envelopes'],
    'PVC ID Cards': ['pvc-id-cards', 'pvc-id-card', 'id-cards-pvc'],
    'Event ID Cards': ['event-id-cards', 'event-id-card'],
    'Multicolour Lanyards': ['multicolour-lanyards', 'lanyards', 'multicolor-lanyards'],
    'Barcode Labels': ['barcode-labels', 'barcode-sticker'],
    'Circle Stickers': ['circle-stickers', 'round-stickers', 'stickers-circle'],
    'Square Stickers': ['square-stickers', 'stickers-square'],
    'Rectangle Stickers': ['rectangle-stickers', 'stickers-rectangle'],
    'Document Printing': ['document-printing', 'documents-printing'],
    'Banner Media': ['banner-media', 'banners', 'flex-banner'],
    'Premium Flex': ['premium-flex', 'flex-printing'],
}

def main():
    print("Validating URL guesses...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    found_map = {}
    
    for product, slugs in GUESSES.items():
        found = False
        for slug in slugs:
            url = f"{BASE_URL}{slug}/"
            try:
                r = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
                if r.status_code == 200:
                    print(f"[FOUND] {product} -> {url}")
                    found_map[product] = url
                    found = True
                    break
                else:
                    # Try without trailing slash
                    url_no_slash = f"{BASE_URL}{slug}"
                    r2 = requests.head(url_no_slash, headers=headers, timeout=5, allow_redirects=True)
                    if r2.status_code == 200:
                         print(f"[FOUND] {product} -> {url_no_slash}")
                         found_map[product] = url_no_slash
                         found = True
                         break
            except Exception as e:
                print(f"Error checking {url}: {e}")
        
        if not found:
            print(f"[MISSING] {product}")

if __name__ == "__main__":
    main()
