from apps.services.models import ServiceCategory, Product

def run():
    # Categories
    categories = [
        ("Book Printing", "book-printing"),
        ("Paper Boxes", "paper-boxes"),
        ("Marketing Material", "marketing-material"),
        ("Stationery", "stationery"),
    ]
    cat_objs = {}
    for name, slug in categories:
        cat, _ = ServiceCategory.objects.get_or_create(name=name, defaults={"slug": slug, "is_active": True})
        cat_objs[name] = cat

    # Products: (name, category, has_design_tool)
    products = [
        ("Children's Book Printing", "Book Printing", False),
        ("Comic Book Printing", "Book Printing", False),
        ("Coffee Table Books", "Book Printing", False),
        ("Coloring Book Printing", "Book Printing", False),
        ("Art Book Printing", "Book Printing", False),
        ("Annual Reports", "Book Printing", False),
        ("Year Book Printing", "Book Printing", False),
        ("On Demand Books", "Book Printing", False),
        ("Paper Boxes", "Paper Boxes", False),
        ("Medical Paper Boxes", "Paper Boxes", False),
        ("Cosmetic Paper Boxes", "Paper Boxes", False),
        ("Retail Paper Boxes", "Paper Boxes", False),
        ("Folding Carton Boxes", "Paper Boxes", False),
        ("Corrugated Boxes", "Paper Boxes", False),
        ("Kraft Boxes", "Paper Boxes", False),
        ("Brochures", "Marketing Material", True),
        ("Catalogue", "Marketing Material", False),
        ("Poster", "Marketing Material", False),
        ("Flyers", "Marketing Material", True),
        ("Dangler", "Marketing Material", False),
        ("Standees", "Marketing Material", False),
        ("Pen Drives", "Marketing Material", False),
        ("Business Cards", "Stationery", True),
        ("Letter Head", "Stationery", True),
        ("Envelopes", "Stationery", False),
        ("Bill Book", "Stationery", True),
        ("ID Cards", "Stationery", False),
        ("Sticker", "Stationery", True),
        ("Document Printing", "Stationery", False),
    ]
    for name, cat, has_tool in products:
        Product.objects.get_or_create(
            name=name,
            category=cat_objs[cat],
            defaults={
                "has_design_tool": has_tool,
                "is_active": True,
                "is_featured": False,
                "slug": name.lower().replace(" ", "-").replace("'", "")
            }
        )

if __name__ == "__main__":
    run()
