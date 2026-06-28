import { useState, useEffect } from 'react';
import Topbar from './components/Topbar';
import Rail from './components/Rail';
import LeftPanel from './components/LeftPanel';
import Stage from './components/Stage';
import RightPanel from './components/RightPanel';
import { ProductModal, ShortcutsModal, ExportModal, PreflightModal } from './components/Modals';
import { ToastProvider, useToast } from './components/ui/Toast';
import { useShortcuts } from './hooks/useShortcuts';
import { useEditor } from './store/editorStore';
import { api } from './services/api';

function Editor() {
  const [modal, setModal] = useState(null); // 'products' | 'shortcuts' | 'export' | 'preflight'
  const engine = useEditor((s) => s.engine);
  const toast = useToast();
  useShortcuts();

  // ── Bootstrap product from URL query params ──────────────────────
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const slug = params.get('product_slug');
    const returnUrl = params.get('return_url') || document.referrer || '/';
    const urlWidthMm    = parseFloat(params.get('width_mm'))  || 0;
    const urlHeightMm   = parseFloat(params.get('height_mm')) || 0;
    const urlPrintSide  = params.get('printing_side') || '';

    useEditor.getState().update({ returnUrl });

    // Read order context from URL params — the product page (Django, port 8000) passes these
    // in the URL because localStorage is NOT shared across different ports (different origins).
    const productIdFromUrl = parseInt(params.get('product_id')) || 0;
    const quantity = parseInt(params.get('quantity')) || 1;
    const cartUrl = params.get('cart_url') || '';
    const csrfToken = params.get('csrf_token') || '';
    let specifications = {};
    try { specifications = JSON.parse(params.get('specs') || '{}'); } catch (_) {}
    if (productIdFromUrl) {
      useEditor.getState().update({
        orderContext: { product_id: productIdFromUrl, quantity, specifications, cart_url: cartUrl, csrf_token: csrfToken },
      });
    }

    if (!slug) return;

    api.initProduct(slug, urlWidthMm || null, urlHeightMm || null, urlPrintSide || null)
      .then(({ product, templates }) => {
      if (!product) {
        console.warn('[Studio] Product not found for slug:', slug);
        return;
      }

      useEditor.getState().update({
        productConfig: product,
        studioTemplates: templates,
      });

      const finalWidth  = urlWidthMm  || product.width_mm;
      const finalHeight = urlHeightMm || product.height_mm;

      // Determine sides: URL param wins, then API response, then default single-sided
      const isTwoSided = urlPrintSide === 'front_back' ||
                         (product.printing_sides || []).length > 1;
      const sides = isTwoSided ? ['front', 'back'] : ['front'];

      useEditor.getState().setProduct({
        id: product.slug,
        category: product.category_name || 'Custom',
        name: product.name,
        width: finalWidth,
        height: finalHeight,
        unit: 'mm',
        bleed: product.bleed_mm ?? 3,
        safe: product.safe_mm ?? 5,
        sides,
      });

      document.title = `Design ${product.name} | Shirsti PrintStudio`;
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Ctrl+S global save ────────────────────────────────────────────
  useEffect(() => {
    const onSave = async () => {
      if (!engine) return;
      await api.saveDesign(engine.serialize());
      toast('Design saved');
    };
    window.addEventListener('ds:save', onSave);
    return () => window.removeEventListener('ds:save', onSave);
  }, [engine, toast]);

  return (
    <div className="app">
      <Topbar
        onOpenProducts={() => setModal('products')}
        onOpenShortcuts={() => setModal('shortcuts')}
        onOpenExport={() => setModal('export')}
        onOpenPreflight={() => setModal('preflight')}
      />
      <RightPanel />
      <Rail />
      <LeftPanel />
      <Stage />

      {modal === 'products'   && <ProductModal    onClose={() => setModal(null)} />}
      {modal === 'shortcuts'  && <ShortcutsModal  onClose={() => setModal(null)} />}
      {modal === 'export'     && <ExportModal     onClose={() => setModal(null)} />}
      {modal === 'preflight'  && <PreflightModal  onClose={() => setModal(null)} />}
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <Editor />
    </ToastProvider>
  );
}
