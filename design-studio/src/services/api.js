// ============================================================
// API SERVICE LAYER
// All network calls go through here. Point BASE_URL at your
// Django backend. Every method has a graceful local fallback
// so the editor works standalone until APIs are wired up.
// ============================================================

const BASE_URL = import.meta.env.VITE_API_BASE || ''; // e.g. https://your-django.com/api
const TOKEN = () => localStorage.getItem('ds_token') || '';

async function request(path, opts = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(TOKEN() ? { Authorization: `Token ${TOKEN()}` } : {}),
      ...(opts.headers || {}),
    },
    ...opts,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

// ---- MOCK DATA (used when BASE_URL is empty) -------------------
const MOCK = {
  fonts: [
    { family: 'Poppins', url: 'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap', category: 'Sans' },
    { family: 'Playfair Display', url: 'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&display=swap', category: 'Serif' },
    { family: 'Bebas Neue', url: 'https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap', category: 'Display' },
    { family: 'Lobster', url: 'https://fonts.googleapis.com/css2?family=Lobster&display=swap', category: 'Script' },
    { family: 'Roboto Mono', url: 'https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap', category: 'Mono' },
    { family: 'Oswald', url: 'https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;600;700&display=swap', category: 'Sans' },
    { family: 'Dancing Script', url: 'https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap', category: 'Script' },
    { family: 'Montserrat', url: 'https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap', category: 'Sans' },
  ],
  graphics: [
    { id: 'g1', name: 'Star', type: 'svg', svg: '<svg viewBox="0 0 24 24" fill="#f5a623"><path d="M12 2l3 7h7l-5.5 4.5 2 7L12 17l-6.5 3.5 2-7L2 9h7z"/></svg>' },
    { id: 'g2', name: 'Heart', type: 'svg', svg: '<svg viewBox="0 0 24 24" fill="#e0457b"><path d="M12 21s-7-4.5-9.5-9C.8 8.5 2.5 5 6 5c2 0 3.2 1.2 4 2.3C10.8 6.2 12 5 14 5c3.5 0 5.2 3.5 3.5 7-2.5 4.5-9.5 9-9.5 9z"/></svg>' },
    { id: 'g3', name: 'Leaf', type: 'svg', svg: '<svg viewBox="0 0 24 24" fill="#2fa84f"><path d="M17 3C9 3 4 8 4 16c0 2 1 4 1 4s4-1 8-5c3-3 4-9 4-12z"/></svg>' },
    { id: 'g4', name: 'Bolt', type: 'svg', svg: '<svg viewBox="0 0 24 24" fill="#2f6fed"><path d="M13 2L4 14h6l-1 8 9-12h-6z"/></svg>' },
  ],
  templates: [
    {
      id: 't1', name: 'Modern Business Card', productId: 'business-card-eu',
      thumb: '#1d2b4f',
      json: null, // a fabric JSON would live here; we generate one on load
    },
  ],
};

export const api = {
  // ---- DESIGN STUDIO INIT (product config + templates in one call) ----
  async initProduct(slug, widthMm, heightMm, printingSide) {
    try {
      let url = `/design-tool/api/studio/product/?slug=${encodeURIComponent(slug)}`;
      if (widthMm)      url += `&width_mm=${widthMm}&height_mm=${heightMm || widthMm}`;
      if (printingSide) url += `&printing_side=${encodeURIComponent(printingSide)}`;
      const data = await request(url);
      if (data.success) return { product: data.product, templates: data.templates };
    } catch (e) { console.warn('[initProduct]', e); }
    return { product: null, templates: [] };
  },

  // ---- FONTS ----
  async getFonts() {
    return MOCK.fonts; // extend later to call Django font library
  },

  // ---- STOCK IMAGES (search) — Pixabay via Django proxy ----
  async searchImages(query, page = 1) {
    try {
      const params = new URLSearchParams({
        q: query || 'business',
        page: String(page),
        per_page: '18',
      });
      const data = await request(`/design-tool/api/pixabay/images/?${params}`);
      if (data && data.success && Array.isArray(data.images) && data.images.length) {
        return data.images.map((img) => ({
          id: img.id,
          thumb: img.thumbnail_url || img.preview_url,
          full: img.large_url || img.preview_url || img.thumbnail_url,
        }));
      }
    } catch (e) {
      console.warn('[searchImages] Pixabay proxy unavailable, using placeholders:', e.message);
    }
    // Graceful fallback (proxy down or Pixabay key missing/invalid)
    return Array.from({ length: 12 }).map((_, i) => ({
      id: `${query}-${page}-${i}`,
      thumb: `https://picsum.photos/seed/${encodeURIComponent(query)}${page}${i}/200/200`,
      full: `https://picsum.photos/seed/${encodeURIComponent(query)}${page}${i}/1200/1200`,
    }));
  },

  // ---- GRAPHICS / SHAPES (SVG cliparts) ----
  async getGraphics(category = '') {
    return MOCK.graphics;
  },

  // ---- TEMPLATES (kept for compatibility, use initProduct instead) ----
  async getTemplates(productId = '') {
    return MOCK.templates;
  },
  async getTemplate(id) {
    try { return await request(`/design-tool/api/static/template/${id}/`); } catch { return null; }
  },

  // ---- UPLOAD user image ----
  async uploadImage(file) {
    if (!BASE_URL) {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve({ url: reader.result });
        reader.readAsDataURL(file);
      });
    }
    const fd = new FormData();
    fd.append('image', file);
    const res = await fetch(`${BASE_URL}/uploads/`, {
      method: 'POST',
      headers: TOKEN() ? { Authorization: `Token ${TOKEN()}` } : {},
      body: fd,
    });
    return res.json();
  },

  // ---- SAVE design to Django (requires login) ----
  async saveDesign(payload) {
    try {
      return await request('/design-tool/api/static/save/', { method: 'POST', body: JSON.stringify(payload) });
    } catch {
      // Fallback: persist to localStorage so work isn't lost
      localStorage.setItem('ds_last_design', JSON.stringify(payload));
      return { id: 'local-' + Date.now(), ...payload };
    }
  },

  // ---- ADD TO CART: POST design + specs directly to Django, then redirect to cart ----
  async addToCart({ productId, quantity, specifications, designJson, cartUrl, csrfToken }) {
    // csrfToken is passed via URL param from the Django product page (cross-origin handoff).
    // Fall back to reading the cookie — works when both apps share the same hostname (same localhost).
    const csrf = csrfToken || (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
    const res = await fetch(`/orders/api/static-product/add/${productId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf,
      },
      body: JSON.stringify({
        quantity,
        specifications,
        design_data: designJson,
      }),
    });
    const data = await res.json();
    if (!data.success) throw new Error(data.message || 'Failed to add to cart');
    window.location.href = data.cart_url || cartUrl || '/orders/cart/';
    return data;
  },

  // ---- FALLBACK: store design in sessionStorage and redirect back (no orderContext) ----
  submitOrder(payload) {
    sessionStorage.setItem('ds_pending_design', JSON.stringify(payload));
    const returnUrl = payload.returnUrl || '/';
    const sep = returnUrl.includes('?') ? '&' : '?';
    window.location.href = `${returnUrl}${sep}has_design=1`;
    return Promise.resolve({ status: 'redirecting' });
  },

  // ---- SAVED DESIGNS GALLERY (localStorage-backed, no auth required) ----
  async listMyDesigns() {
    try { return JSON.parse(localStorage.getItem('ds_my_designs') || '[]'); }
    catch { return []; }
  },
  async saveNamedDesign({ name, thumb, design }) {
    const list = await this.listMyDesigns();
    const item = { id: 'd-' + Date.now(), name, thumb, design, ts: Date.now() };
    localStorage.setItem('ds_my_designs', JSON.stringify([item, ...list].slice(0, 30)));
    return item;
  },
  async deleteMyDesign(id) {
    const list = await this.listMyDesigns();
    localStorage.setItem('ds_my_designs', JSON.stringify(list.filter((d) => d.id !== id)));
    return { ok: true };
  },
};
