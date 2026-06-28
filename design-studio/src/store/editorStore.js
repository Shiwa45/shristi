import { create } from 'zustand';
import { PRODUCT_PRESETS } from '../config/printConfig';

// ============================================================
// EDITOR STORE
// Holds UI state + a reference to the live fabric canvas engine.
// The engine itself manages the canvas; the store mirrors what
// the React panels need to render (layers, selection, etc).
// ============================================================

export const useEditor = create((set, get) => ({
  engine: null,            // CanvasEngine instance
  setEngine: (engine) => set({ engine }),

  product: PRODUCT_PRESETS[1], // default: EU business card
  sides: ['front'],
  activeSide: 'front',

  // Django product config loaded from URL params + API
  productConfig: null,       // raw API response { id, name, slug, width_mm, height_mm, ... }
  studioTemplates: [],       // StaticProductTemplate[] from Django
  returnUrl: '/',            // where to go after cancel / close

  // Order context stored by the product page in localStorage before opening the studio.
  // Shape: { product_id, quantity, specifications, cart_url, ts }
  orderContext: null,

  zoom: 1,
  unit: 'mm',

  // toggles for print guides
  showBleed: true,
  showSafe: true,
  showTrim: true,
  showGrid: false,
  showRulers: true,
  snapToGuides: true,

  // mirrored canvas state
  layers: [],              // [{id,name,type,visible,locked,selected}]
  selectedIds: [],
  activeObjectProps: null, // props of the single selected object

  canUndo: false,
  canRedo: false,

  // left panel active tab
  activePanel: 'templates', // templates|elements|text|images|uploads|layers

  set,
  update: (patch) => set(patch),

  setActivePanel: (p) => set({ activePanel: p }),
  setUnit: (unit) => set({ unit }),

  toggleGuide: (key) => set((s) => ({ [key]: !s[key] })),

  setProduct: (product) => {
    set({ product, sides: product.sides, activeSide: product.sides[0] });
    get().engine?.applyProduct(product);
  },

  setActiveSide: (side) => {
    set({ activeSide: side });
    get().engine?.switchSide(side);
  },
}));
