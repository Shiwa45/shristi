// ============================================================
// PRINT CONFIGURATION
// Central place for DPI, units, bleed/safe defaults, products.
// Change DPI here and the whole editor recalculates.
// ============================================================

export const DPI = 300; // print resolution. 300 is standard for print.
export const SCREEN_DPI = 96;

// Convert real-world units -> pixels at our working DPI.
export const MM_PER_INCH = 25.4;
export const mmToPx = (mm, dpi = DPI) => (mm / MM_PER_INCH) * dpi;
export const inToPx = (inch, dpi = DPI) => inch * dpi;
export const pxToMm = (px, dpi = DPI) => (px / dpi) * MM_PER_INCH;
export const cmToPx = (cm, dpi = DPI) => mmToPx(cm * 10, dpi);

// Default print margins (in mm)
export const DEFAULT_BLEED_MM = 3;   // area that gets trimmed off
export const DEFAULT_SAFE_MM = 5;    // keep important content inside this

// Visual indicators
export const GUIDE_COLORS = {
  bleed: '#e0457b',   // pink/magenta — outer trim
  trim: '#2f6fed',    // blue — final cut line (the document edge)
  safe: '#2fa84f',    // green — safe zone for text/logos
};

// ============================================================
// PRODUCT PRESETS — extend freely / load from Django later.
// dimensions are the FINAL trim size (what the customer receives)
// ============================================================
export const PRODUCT_PRESETS = [
  {
    id: 'business-card-us',
    category: 'Cards',
    name: 'Business Card (US)',
    width: 88.9, height: 50.8, unit: 'mm', // 3.5 x 2 in
    bleed: 3, safe: 4,
    sides: ['front', 'back'],
  },
  {
    id: 'business-card-eu',
    category: 'Cards',
    name: 'Business Card (EU)',
    width: 85, height: 55, unit: 'mm',
    bleed: 3, safe: 4,
    sides: ['front', 'back'],
  },
  {
    id: 'flyer-a5',
    category: 'Flyers',
    name: 'Flyer A5',
    width: 148, height: 210, unit: 'mm',
    bleed: 3, safe: 5,
    sides: ['front', 'back'],
  },
  {
    id: 'flyer-a4',
    category: 'Flyers',
    name: 'Flyer A4',
    width: 210, height: 297, unit: 'mm',
    bleed: 3, safe: 5,
    sides: ['front', 'back'],
  },
  {
    id: 'poster-a3',
    category: 'Posters',
    name: 'Poster A3',
    width: 297, height: 420, unit: 'mm',
    bleed: 3, safe: 8,
    sides: ['front'],
  },
  {
    id: 'postcard',
    category: 'Cards',
    name: 'Postcard',
    width: 148, height: 105, unit: 'mm',
    bleed: 3, safe: 5,
    sides: ['front', 'back'],
  },
  {
    id: 'sticker-square',
    category: 'Stickers',
    name: 'Square Sticker 3in',
    width: 76.2, height: 76.2, unit: 'mm',
    bleed: 2, safe: 3,
    sides: ['front'],
  },
  {
    id: 'banner-roll',
    category: 'Large Format',
    name: 'Roll-up Banner',
    width: 850, height: 2000, unit: 'mm',
    bleed: 5, safe: 30,
    sides: ['front'],
  },
  {
    id: 'tshirt-print',
    category: 'Apparel',
    name: 'T-Shirt Print Area',
    width: 280, height: 350, unit: 'mm',
    bleed: 0, safe: 10,
    sides: ['front', 'back'],
  },
  {
    id: 'custom',
    category: 'Custom',
    name: 'Custom Size',
    width: 100, height: 100, unit: 'mm',
    bleed: 3, safe: 5,
    sides: ['front'],
  },
];

export const UNIT_OPTIONS = ['mm', 'cm', 'in', 'px'];

export const toPx = (value, unit, dpi = DPI) => {
  switch (unit) {
    case 'mm': return mmToPx(value, dpi);
    case 'cm': return cmToPx(value, dpi);
    case 'in': return inToPx(value, dpi);
    case 'px': return value;
    default: return value;
  }
};

export const fromPx = (px, unit, dpi = DPI) => {
  switch (unit) {
    case 'mm': return pxToMm(px, dpi);
    case 'cm': return pxToMm(px, dpi) / 10;
    case 'in': return px / dpi;
    case 'px': return px;
    default: return px;
  }
};
