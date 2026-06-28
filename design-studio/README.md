# PrintStudio — Standalone Product Design Tool

A React + Fabric.js print design editor for product personalization (business cards, flyers, posters, stickers, apparel, banners). Built to run standalone and connect to a Django backend later.

## Quick start

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production build -> dist/
```

## What's included

**Print-ready canvas**
- Real-world units (mm / cm / in / px) at a configurable print DPI (default 300 — see `src/config/printConfig.js`).
- **Bleed**, **Trim**, and **Safe** guide lines drawn automatically per product, with on/off toggles. Mandatory for print; excluded from exports.
- Bleed is added around the document; PNG export can include or exclude it.
- Optional grid + center snapping.

**Editing**
- Text (multi-line textbox, font family from API, size, weight, italic, underline, alignment, letter spacing, line height, color, **curved/arc text**).
- Shapes: rect (corner radius), circle, ellipse, triangle, line, **pentagon, hexagon, octagon, star, heart, arrow, speech bubble**.
- SVG graphics/cliparts (from API).
- **QR code generator** (URL/text, custom color, transparent background).
- **Free-draw / pencil brush** with adjustable color & width.
- Images (stock search via API, user uploads, drag & drop) with **filters** (B&W, sepia, invert, brightness, contrast, saturation, blur) and image replace.
- **Gradient fills** (linear/radial) and **drop shadows** on any object.
- Per-object: position, size, rotation, fill, stroke, opacity, flip, align (to trim box), distribute, lock, visibility.
- **Canvas background color**.
- Layers panel: reorder, rename, hide, lock, select.
- Group / ungroup, duplicate, copy/paste, full undo/redo history.
- Multi-side products (front / back) with independent canvases.
- **Saved designs gallery** — save named designs with thumbnails and reload them later.
- **Print preflight check** — flags content outside the safe area and low-resolution (<150 DPI) images before ordering.

**Keyboard shortcuts** (desktop/laptop) — see the keyboard icon in the toolbar.
Undo/redo, duplicate, copy/paste, group, layer order, delete, arrow-key nudge (x10 with Shift), lock, zoom, fit, save, escape.

**SVG templates** — loaded as fully-editable objects (`engine.loadSvgTemplate(svgString)`), positioned inside the bleed.

**Export** — PNG (with/without bleed, 1-4x scale), SVG (vectors), JSON (editable state for re-loading).

## Connecting to Django

All network calls live in `src/services/api.js`. With no backend configured the editor uses local mocks/fallbacks so it works fully standalone. To connect:

1. Create `.env`:
   ```
   VITE_API_BASE=https://your-site.com/api
   ```
2. Implement these endpoints (auth via `Token` header, token read from `localStorage.ds_token`):

| Method | Endpoint | Purpose | Response shape |
|---|---|---|---|
| GET  | `/fonts/` | font list | `[{ family, url, category }]` |
| GET  | `/graphics/?category=` | SVG cliparts | `[{ id, name, svg }]` |
| GET  | `/images/?q=&page=` | stock image search | `[{ id, thumb, full }]` |
| GET  | `/templates/?product=` | template list | `[{ id, name, productId, thumb, json }]` |
| GET  | `/templates/:id/` | single template | `{ id, name, json }` (fabric JSON or `svg`) |
| POST | `/uploads/` | user image upload (multipart `image`) | `{ url }` |
| POST | `/designs/` | save design | echo + `{ id }` |
| POST | `/orders/` | submit order | `{ orderId, status }` |
| GET  | `/my-designs/` | list user's saved designs | `[{ id, name, thumb, design, ts }]` |
| POST | `/my-designs/` | save named design | `{ id, name, thumb, design }` |
| DELETE | `/my-designs/:id/` | delete a saved design | `{ ok: true }` |

3. The order payload sent to `/orders/` contains:
   ```json
   {
     "design":  { "product": {}, "sides": { "front": {}, "back": {} }, "activeSide": "front" },
     "preview": "data:image/png;base64,...",
     "print":   "data:image/png;base64,...",
     "product": {}
   }
   ```
   `preview` = low-res no bleed; `print` = full-res with bleed. Decode `print` server-side for the print-ready file, or re-render the fabric JSON at full DPI.

## Products & sizes

Edit `PRODUCT_PRESETS` in `src/config/printConfig.js`, or load them from Django and call `useEditor.getState().setProduct(p)`. Each preset defines final trim `width/height`, `unit`, `bleed`, `safe`, and `sides`.

## Embedding in your Django site

Build (`npm run build`) and serve `dist/` as static files, or mount in an iframe/route. To pass context in (preselected product, user token), read it from the URL/query in `App.jsx` and call `setProduct` / set `localStorage.ds_token` on load.

## Architecture

```
src/
  config/printConfig.js   units, DPI, product presets, guide colors
  services/api.js         all backend calls (+ standalone mocks)
  store/editorStore.js    Zustand UI/editor state
  canvas/CanvasEngine.js  Fabric.js wrapper: guides, history, sides, export
  hooks/useShortcuts.js   keyboard shortcuts
  components/             Topbar, Rail, LeftPanel, Stage, RightPanel, Modals
```

The `CanvasEngine` is framework-agnostic — all canvas logic lives there; React only renders panels and reflects state.
