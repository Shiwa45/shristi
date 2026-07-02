from django.core.management.base import BaseCommand
from apps.services.models import StaticProduct

DESCRIPTIONS = {
    # ── BOOK PRINTING ─────────────────────────────────────────────────────────
    "childrens-book-printing": {
        "description": (
            "Bring stories to life with Shristi's Children's Book Printing — vibrant colours, "
            "safe materials, and durable binding make every page a delight. Whether it's a "
            "picture book, early-reader, or educational title, we handle full-colour offset "
            "printing on high-quality art paper with soft-cover or hard-cover options. "
            "Custom sizes, round-corner pages, and UV-coated covers give your book a premium "
            "feel that young readers will love."
        ),
        "short_description": "Vibrant, durable children's books printed with safe materials and full-colour offset quality.",
    },
    "comic-book-printing": {
        "description": (
            "Shristi's Comic Book Printing delivers razor-sharp line art and punchy colours "
            "that make every panel pop. We offer saddle-stitch and perfect-bound formats on "
            "glossy or matte art paper, ideal for indie creators, school projects, and "
            "marketing campaigns. Fast turnaround, bulk discounts, and custom cover finishes "
            "ensure your comic stands out on any shelf."
        ),
        "short_description": "Sharp, vivid comic books with custom binding and glossy finishes for indie creators and brands.",
    },
    "coffee-table-book-printing": {
        "description": (
            "Impress clients and guests with a beautifully crafted Coffee Table Book from "
            "Shristi. Printed on thick art paper with rich, true-to-life colour reproduction, "
            "our coffee table books are perfect for portfolios, corporate gifting, real-estate "
            "showcases, and wedding memories. Choose from a range of hard-cover finishes, "
            "ribbon bookmarks, and premium lamination to create a keepsake that lasts a lifetime."
        ),
        "short_description": "Stunning hardcover coffee table books on premium art paper — perfect for gifting and showcasing.",
    },
    "coloring-book-printing": {
        "description": (
            "Shristi's Coloring Book Printing combines crisp black-and-white line artwork "
            "with sturdy paper that handles markers, coloured pencils, and crayons without "
            "bleed-through. Ideal for children's activity books, mindfulness journals, and "
            "branded giveaways, our colouring books can be saddle-stitched or spiral-bound "
            "so pages lie flat while in use. Custom cover design and bulk pricing available."
        ),
        "short_description": "Crisp coloring books on bleed-proof paper with spiral or saddle-stitch binding.",
    },
    "art-book-printing": {
        "description": (
            "Showcase your artwork in its best form with Shristi's Art Book Printing. "
            "We use high-definition offset printing on premium art paper to reproduce every "
            "brushstroke, gradient, and texture with exceptional fidelity. Perfect for "
            "galleries, fine-art portfolios, exhibition catalogues, and artist monographs, "
            "our art books come in custom sizes with linen-wrapped covers, matte or gloss "
            "lamination, and sewn-spine binding for a museum-quality result."
        ),
        "short_description": "Museum-quality art books with high-definition colour reproduction on premium art paper.",
    },
    "annual-reports-printing": {
        "description": (
            "Make a lasting impression on stakeholders with Shristi's Annual Reports Printing. "
            "We produce professional, board-quality reports with sharp text, accurate "
            "infographic colours, and premium paper stocks that reflect your company's "
            "credibility. Available in A4 and custom sizes with soft-cover or hard-cover "
            "binding, matte lamination, and spot-UV highlights — delivered on time, "
            "every time, to meet your AGM deadlines."
        ),
        "short_description": "Professional annual reports with premium binding and accurate colour — ready before your AGM.",
    },
    "year-book-printing": {
        "description": (
            "Capture memories that last a lifetime with Shristi's Yearbook Printing. "
            "Designed for schools, colleges, and organisations, our yearbooks feature "
            "vibrant full-colour photo printing, durable case-bound covers, and custom "
            "layouts that tell your community's story. From class photos and achievement "
            "sections to advertisements and messages, every page is printed to the "
            "highest standard with bulk pricing that fits your budget."
        ),
        "short_description": "Beautiful, case-bound yearbooks for schools and organisations with full-colour photo printing.",
    },
    "on-demand-books-printing": {
        "description": (
            "No minimum order, no wasted stock — Shristi's On-Demand Book Printing lets "
            "you print exactly the quantity you need, when you need it. Ideal for "
            "self-publishers, training manuals, event programmes, and limited-edition "
            "releases, our digital print process delivers consistent quality from a single "
            "copy to a few hundred. Fast turnaround, multiple binding options, and "
            "competitive per-copy pricing make printing on demand the smart choice."
        ),
        "short_description": "Print any quantity on demand — no minimum order, fast delivery, consistent quality every time.",
    },

    # ── PAPER BOXES ───────────────────────────────────────────────────────────
    "paper-bag": {
        "description": (
            "Shristi's custom Paper Bags are the perfect branded touch for retail, "
            "gifting, and events. Crafted from sturdy kraft or art paper with reinforced "
            "handles, our bags are available in a range of sizes and can be printed in "
            "full colour with your logo and design. Eco-friendly options, glossy and matte "
            "lamination, and foil-stamping finishes make your packaging as memorable as "
            "what's inside."
        ),
        "short_description": "Branded paper bags in kraft or art paper with full-colour printing — eco-friendly and stylish.",
    },
    "custom-paper-boxes-1": {
        "description": (
            "Elevate your product presentation with Shristi's Custom Paper Boxes. "
            "Engineered for strength and designed for impact, our boxes can be tailored "
            "to any shape, size, or print specification. From luxury rigid boxes for "
            "premium goods to lightweight folding cartons for retail, we deliver precise "
            "die-cutting, vibrant offset printing, and premium lamination finishes that "
            "make unboxing an experience in itself."
        ),
        "short_description": "Custom-shaped paper boxes with precision die-cutting and vibrant printing for any product.",
    },
    "custom-paper-boxes": {
        "description": (
            "Elevate your product presentation with Shristi's Custom Paper Boxes. "
            "Engineered for strength and designed for impact, our boxes can be tailored "
            "to any shape, size, or print specification. From luxury rigid boxes for "
            "premium goods to lightweight folding cartons for retail, we deliver precise "
            "die-cutting, vibrant offset printing, and premium lamination finishes that "
            "make unboxing an experience in itself."
        ),
        "short_description": "Custom-shaped paper boxes with precision die-cutting and vibrant printing for any product.",
    },
    "kraft-paper-product-box-1": {
        "description": (
            "Shristi's Kraft Paper Product Boxes combine natural aesthetics with "
            "outstanding durability. The earthy brown texture of kraft paper gives your "
            "packaging a rustic, eco-conscious look that resonates with modern consumers. "
            "Available in multiple sizes, these boxes can be printed with your brand "
            "details, finished with a matte laminate, or left plain for a truly "
            "minimalist appeal — ideal for handmade products, bakeries, and organic brands."
        ),
        "short_description": "Durable kraft paper boxes with a natural, eco-friendly look — ideal for artisan and organic brands.",
    },
    "kraft-paper-product-box": {
        "description": (
            "Shristi's Kraft Paper Product Boxes combine natural aesthetics with "
            "outstanding durability. The earthy brown texture of kraft paper gives your "
            "packaging a rustic, eco-conscious look that resonates with modern consumers. "
            "Available in multiple sizes, these boxes can be printed with your brand "
            "details, finished with a matte laminate, or left plain for a truly "
            "minimalist appeal — ideal for handmade products, bakeries, and organic brands."
        ),
        "short_description": "Durable kraft paper boxes with a natural, eco-friendly look — ideal for artisan and organic brands.",
    },
    "hang-tags-1": {
        "description": (
            "Add a professional finishing touch to your products with Shristi's custom "
            "Hang Tags. Printed on 300–350 GSM art paper with precise die-cut shapes, "
            "our hang tags can carry your logo, price, care instructions, and brand "
            "story in style. Choose from matte or glossy lamination, foil accents, and "
            "a variety of sizes and shapes to make your products stand out on any rack "
            "or shelf."
        ),
        "short_description": "Custom die-cut hang tags on premium art paper with foil and lamination options.",
    },
    "hang-tags": {
        "description": (
            "Add a professional finishing touch to your products with Shristi's custom "
            "Hang Tags. Printed on 300–350 GSM art paper with precise die-cut shapes, "
            "our hang tags can carry your logo, price, care instructions, and brand "
            "story in style. Choose from matte or glossy lamination, foil accents, and "
            "a variety of sizes and shapes to make your products stand out on any rack "
            "or shelf."
        ),
        "short_description": "Custom die-cut hang tags on premium art paper with foil and lamination options.",
    },
    "stickers-labels": {
        "description": (
            "From product labelling to packaging seals, Shristi's Stickers & Labels "
            "are printed on high-quality materials including paper, PVC vinyl, and "
            "transparent films. Our labels are available in any shape or size with "
            "strong adhesive backing that sticks to glass, plastic, metal, and paper. "
            "Full-colour printing, waterproof options, and custom finishes ensure "
            "your brand looks sharp in every application."
        ),
        "short_description": "Custom stickers and labels in paper or vinyl — waterproof, full-colour, any shape or size.",
    },

    # ── MARKETING MATERIAL ────────────────────────────────────────────────────
    "brochures": {
        "description": (
            "Shristi's Brochures are designed to inform, impress, and convert. "
            "Available in Bi-fold and Tri-fold formats on 300 GSM gloss or matt art paper "
            "with premium lamination, our brochures deliver sharp images and vivid colours "
            "that represent your brand at its best. Whether for trade shows, retail counters, "
            "or direct mail campaigns, our brochures communicate your message clearly and "
            "leave a lasting impression on every reader."
        ),
        "short_description": "Professional bi-fold & tri-fold brochures on 300 GSM art paper — bold colours, premium lamination.",
    },
    "button-badges": {
        "description": (
            "Make your brand wearable with Shristi's custom Button Badges. "
            "Available in 40 mm and 60 mm diameter sizes, these pin-back badges feature "
            "full-colour printing protected under a clear dome cover for long-lasting "
            "vibrancy. Perfect for events, campaigns, school fairs, and promotional "
            "giveaways, button badges are a fun and cost-effective way to spread your "
            "message wherever people go."
        ),
        "short_description": "Full-colour button badges in 40 mm and 60 mm sizes — great for events and promotions.",
    },
    "certificates": {
        "description": (
            "Recognise achievement in style with Shristi's premium Certificates. "
            "Printed on 300–350 GSM art paper in A3, A4, and A5 sizes, our certificates "
            "feature crisp text, rich colours, and a professional finish that makes "
            "every recipient feel truly valued. Ideal for schools, corporates, and "
            "award ceremonies, we offer bulk printing with fast turnaround so you're "
            "always ready for your next event."
        ),
        "short_description": "Premium A3/A4/A5 certificates on art paper — sharp, colourful, and ready for any award ceremony.",
    },
    "custom-roll-up-standees": {
        "description": (
            "Command attention at any event with Shristi's Custom Roll-Up Standees. "
            "Printed on premium flex or banner media with optional matte or gloss finish, "
            "our standees deliver bold, high-resolution graphics that draw eyes from "
            "across the room. Available in 2×5 and 2.5×6 feet sizes with sturdy "
            "retractable bases, they are quick to set up, easy to transport, and built "
            "to last through multiple events."
        ),
        "short_description": "Bold, retractable roll-up standees in 2×5 & 2.5×6 ft — perfect for events and exhibitions.",
    },
    "danglers": {
        "description": (
            "Grab shopper attention right at the point of sale with Shristi's custom "
            "Danglers. Available in Normal, Classic, Round, and fully custom shapes "
            "across multiple sizes, our danglers are printed on 250–300 GSM paper with "
            "matte or gloss lamination for eye-catching durability. Hung from ceilings, "
            "shelves, or displays, they are a proven way to boost in-store visibility "
            "for promotions, offers, and new product launches."
        ),
        "short_description": "Eye-catching custom danglers in multiple shapes and sizes — boost in-store visibility instantly.",
    },
    "flyers-leaflets": {
        "description": (
            "Shristi's Flyers & Leaflets are your most affordable and versatile "
            "marketing tool. Available from A3 to A7 and DL sizes on paper stocks "
            "ranging from 75 GSM to 250 GSM art paper, in single or four-colour printing "
            "on one or both sides. Perfect for restaurant menus, event announcements, "
            "discount offers, and awareness drives — printed in large quantities at "
            "budget-friendly rates without compromising on quality."
        ),
        "short_description": "Affordable flyers & leaflets in A3–A7 sizes with single or full-colour printing on any paper.",
    },
    "poster": {
        "description": (
            "Make a bold statement with Shristi's high-quality Poster Printing. "
            "Available in A3 and A4 sizes on 170–300 GSM paper with optional matte or "
            "gloss lamination and glued-edge finishing, our posters are perfect for "
            "promotions, events, offices, and retail displays. Vibrant, fade-resistant "
            "inks ensure your visuals stay sharp and impactful wherever they're displayed."
        ),
        "short_description": "Bold A3/A4 posters on 170–300 GSM paper with optional lamination and glued edges.",
    },
    "tent-cards": {
        "description": (
            "Shristi's Tent Cards are the ideal table-top marketing tool for restaurants, "
            "hotels, conferences, and retail counters. Available in A4, A5, and A6 sizes "
            "in portrait or landscape orientation, printed on 250–300 GSM art paper with "
            "a sharp crease for a sturdy, self-standing finish. Customise both sides "
            "to feature menus, offers, event details, or brand messaging that engages "
            "customers right where they sit."
        ),
        "short_description": "Self-standing tent cards in A4/A5/A6 on 250–300 GSM art paper — ideal for tables and counters.",
    },

    # ── STATIONERY ────────────────────────────────────────────────────────────
    "bill-book": {
        "description": (
            "Shristi's Bill Books keep your business transactions organised and "
            "professional. Available in Black & White and full-colour formats with "
            "Original + Duplicate/Triplicate/Quadruplicate sets, our bill books use "
            "high-quality NCR paper in your choice of pink, yellow, light green, or "
            "light blue for duplicate sheets. Optional sequential invoice numbering "
            "ensures accurate record-keeping for shops, service providers, and freelancers."
        ),
        "short_description": "Custom NCR bill books with invoice numbering — available in B&W or colour, any duplicate set.",
    },
    "business-cards": {
        "description": (
            "Your business card is the first impression you leave behind — make it "
            "count with Shristi's premium Business Cards. Choose from five distinct "
            "styles: Standard, Non-Tear, Raised Foil, Raised Spot-UV, and Texture cards "
            "on specialty paper stocks. Each option offers unique finishes that reflect "
            "your professional identity, from subtle elegance to bold luxury, with "
            "full-colour offset printing and fast delivery."
        ),
        "short_description": "Premium business cards in 5 styles — Standard, Non-Tear, Foil, Spot-UV & Texture — from Shristi.",
    },
    "envelopes": {
        "description": (
            "Complete your corporate identity with Shristi's custom printed Envelopes. "
            "Available in DL (10×4.5), A5, and A6 sizes on 80–120 GSM paper, our "
            "envelopes can be printed in black & white or full colour with your logo, "
            "return address, and brand colours. Ideal for offices, courier services, "
            "and official correspondence — ordered in quantities from 100 to 3000 at "
            "competitive bulk rates."
        ),
        "short_description": "Branded envelopes in DL/A5/A6 with B&W or colour printing — available from 100 to 3000 qty.",
    },
    "id-cards-lanyards": {
        "description": (
            "Shristi's ID Cards & Lanyards solution covers all your staff, event, and "
            "institutional identification needs. Choose from Event ID Cards printed on "
            "coated stock with matte or glossy lamination, durable PVC ID Cards with "
            "portrait or landscape orientation, or Multicolour Lanyards with SD lever "
            "hook attachments. All options are available in quantities from 100 to 3000 "
            "with fast turnaround and competitive bulk pricing."
        ),
        "short_description": "Complete ID card and lanyard solutions — event cards, PVC cards, and multicolour lanyards.",
    },
    "letter-head": {
        "description": (
            "A well-designed letterhead communicates professionalism before a word is "
            "read. Shristi offers Corporate and Standard Letter Heads printed on A4 "
            "JK Excel Bond Paper or DO Paper (100 GSM) in both single-side and both-side "
            "formats. Crisp, accurate colour reproduction keeps your branding consistent "
            "across all official communications — available in quantities from 200 to "
            "2000 sheets with bulk pricing."
        ),
        "short_description": "Professional A4 letterheads on JK Excel Bond or DO Paper — corporate or standard, any quantity.",
    },
    "sticker": {
        "description": (
            "Shristi's Sticker range covers every labelling and branding need with "
            "eight specialised types: Address Labels, Barcode Labels, Circle Stickers, "
            "Custom Stickers, Product Labels, Rectangle Stickers, Square Stickers, and "
            "Warning Labels. Available on paper (chromo), PVC vinyl, transparent vinyl, "
            "dome, and front-transparent materials in a wide range of sizes and shapes — "
            "with strong adhesive and waterproof options for indoor and outdoor use."
        ),
        "short_description": "8 sticker types — address, barcode, product, warning & more — in paper, vinyl or dome material.",
    },
}


class Command(BaseCommand):
    help = "Set pre-written descriptions for all active StaticProducts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite products that already have descriptions",
        )

    def handle(self, *args, **options):
        products = (
            StaticProduct.objects.filter(is_active=True)
            .select_related("category")
            .order_by("category__name", "name")
        )

        updated = 0
        skipped = 0
        missing = 0

        for product in products:
            data = DESCRIPTIONS.get(product.slug)

            if not data:
                self.stderr.write(f"  [NO ENTRY] {product.slug} — add a description for this product")
                missing += 1
                continue

            has_content = bool(
                product.description and product.description.strip()
                and product.short_description and product.short_description.strip()
            )

            if has_content and not options["overwrite"]:
                self.stdout.write(f"  [skip] {product.name}")
                skipped += 1
                continue

            product.description = data["description"]
            product.short_description = data["short_description"]
            product.save(update_fields=["description", "short_description"])
            self.stdout.write(self.style.SUCCESS(f"  [ok]   {product.name}"))
            updated += 1

        self.stdout.write(f"\nDone — updated: {updated}, skipped: {skipped}, missing: {missing}")
