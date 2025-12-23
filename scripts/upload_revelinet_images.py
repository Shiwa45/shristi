"""
Utility script to copy local static product images into media storage and
attach them to the matching StaticProduct entries.
"""

import os
import shutil
import sys
from pathlib import Path

import django
from django.utils.text import slugify

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shirsti_printing.settings")
django.setup()

from apps.services.models import StaticProduct  # noqa: E402


def copy_and_attach(mapping, target_field, destination):
    """
    Copy images based on mapping and set the given FileField on products.

    Args:
        mapping (dict[str, str]): filename -> product name.
        target_field (str): model field to update ("featured_image"/"hero_image").
        destination (Path): absolute path where files should be copied.
    """
    results = []
    media_root = BASE_DIR / "media"
    destination.mkdir(parents=True, exist_ok=True)
    relative_dir = destination.relative_to(media_root)

    for filename, product_name in mapping.items():
        source_path = BASE_DIR / "static" / "prducts" / filename
        if not source_path.exists():
            results.append(f"Missing source file: {filename}")
            continue

        try:
            product = StaticProduct.objects.get(name=product_name)
        except StaticProduct.DoesNotExist:
            results.append(f"Product not found: {product_name}")
            continue

        dest_name = f"{slugify(product_name)}{source_path.suffix.lower()}"
        dest_path = destination / dest_name

        shutil.copy2(source_path, dest_path)
        setattr(product, target_field, str(relative_dir / dest_name))
        product.save(update_fields=[target_field])

        results.append(f"Updated {product_name} -> {relative_dir / dest_name} ({target_field})")

    return results


def main():
    featured_map = {
        "barcode.jpeg": "Barcode Labels",
        "Business Card.jpeg": "Standard Business Card",
        "Business Card2.jpeg": "TEXTURE BUSINESS CARD",
        "Circle Stickers.jpeg": "Circle Stickers",
        "Letter Head.jpeg": "Standard Letter Head",
        "Letter Head2.jpeg": "Corporate Letter Head",
        "Multicolour Lanyards.jpeg": "Multicolour Lanyards",
        "On-Demand Books.jpeg": "on Demand Books Printing",
        "Paper Bag.jpeg": "Paper Bag",
        "poster.jpeg": "Banner Media",
        "poster2.jpeg": "Premium Flex",
        "Warning Labels.jpeg": "Warning Labels",
    }

    hero_map = {
        "Paper Bag2.jpeg": "Paper Bag",
        "Standees.jpeg": "Premium Flex",
    }

    featured_dir = BASE_DIR / "media" / "products" / "featured"
    hero_dir = BASE_DIR / "media" / "products" / "hero"

    print("Processing featured images...")
    for line in copy_and_attach(featured_map, "featured_image", featured_dir):
        print(line)

    print("\nProcessing hero images...")
    for line in copy_and_attach(hero_map, "hero_image", hero_dir):
        print(line)


if __name__ == "__main__":
    main()
