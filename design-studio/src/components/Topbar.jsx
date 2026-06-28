import { useState } from 'react';
import {
  Undo2, Redo2, Copy, Trash2, Group, Ungroup, Lock,
  ArrowUpToLine, ArrowDownToLine, Keyboard, Download, Save,
  ShoppingCart, Settings2, Sparkles, ShieldCheck, Loader2,
} from 'lucide-react';
import { useEditor } from '../store/editorStore';
import { useToast } from './ui/Toast';
import { api } from '../services/api';

export default function Topbar({ onOpenProducts, onOpenShortcuts, onOpenExport, onOpenPreflight }) {
  const engine = useEditor((s) => s.engine);
  const canUndo = useEditor((s) => s.canUndo);
  const canRedo = useEditor((s) => s.canRedo);
  const product = useEditor((s) => s.product);
  const toast = useToast();
  const [adding, setAdding] = useState(false);

  const save = async () => {
    if (!engine) return;
    const payload = engine.serialize();
    await api.saveDesign(payload);
    toast('Design saved');
  };

  const returnUrl = useEditor((s) => s.returnUrl);
  const productConfig = useEditor((s) => s.productConfig);
  const orderContext = useEditor((s) => s.orderContext);

  const order = async () => {
    if (!engine || adding) return;
    setAdding(true);

    try {
      const designJson = engine.serialize();

      if (orderContext?.product_id) {
        // Direct cart submission — specs came from the product page
        await api.addToCart({
          productId    : orderContext.product_id,
          quantity     : orderContext.quantity || 1,
          specifications: orderContext.specifications || {},
          designJson,
          cartUrl      : orderContext.cart_url || '/orders/cart/',
          csrfToken    : orderContext.csrf_token || '',
        });
        // addToCart redirects on success; no toast needed
      } else {
        // Fallback: no orderContext (standalone studio launch) — redirect back to product page
        const preview = engine.exportPNG({ includeBleed: false, multiplier: 0.5 });
        await api.submitOrder({
          design: designJson,
          preview,
          product: productConfig || product,
          returnUrl,
        });
      }
    } catch (err) {
      toast(`Could not add to cart: ${err.message}`);
      setAdding(false);
    }
  };

  return (
    <header className="topbar">
      <div className="brand">
        <span className="mark"><Sparkles size={16} color="#fff" /></span>
        Easyian PrintStudio
      </div>
      <span className="sep" />
      <button className="btn ghost" onClick={onOpenProducts}>
        <Settings2 size={15} /> {product.name}
      </button>
      <span className="sep" />

      <button className="iconbtn" title="Undo (Ctrl+Z)" disabled={!canUndo} onClick={() => engine.undo()}><Undo2 size={17} /></button>
      <button className="iconbtn" title="Redo (Ctrl+Shift+Z)" disabled={!canRedo} onClick={() => engine.redo()}><Redo2 size={17} /></button>
      <span className="sep" />
      <button className="iconbtn" title="Duplicate (Ctrl+D)" onClick={() => engine.duplicateSelected()}><Copy size={17} /></button>
      <button className="iconbtn" title="Group (Ctrl+G)" onClick={() => engine.group()}><Group size={17} /></button>
      <button className="iconbtn" title="Ungroup (Ctrl+Shift+G)" onClick={() => engine.ungroup()}><Ungroup size={17} /></button>
      <button className="iconbtn" title="Bring to front (Ctrl+])" onClick={() => engine.bringToFront()}><ArrowUpToLine size={17} /></button>
      <button className="iconbtn" title="Send to back (Ctrl+[)" onClick={() => engine.sendToBack()}><ArrowDownToLine size={17} /></button>
      <button className="iconbtn" title="Lock (L)" onClick={() => engine.toggleLock()}><Lock size={17} /></button>
      <button className="iconbtn" title="Delete (Del)" onClick={() => engine.deleteSelected()}><Trash2 size={17} /></button>

      <div className="spacer" />

      <button className="iconbtn" title="Shortcuts" onClick={onOpenShortcuts}><Keyboard size={18} /></button>
      <button className="btn" onClick={onOpenPreflight}><ShieldCheck size={15} /> Preflight</button>
      <button className="btn" onClick={onOpenExport}><Download size={15} /> Export</button>
      <button className="btn" onClick={save}><Save size={15} /> Save</button>
      <button className="btn primary" onClick={order} disabled={adding}>
        {adding ? <Loader2 size={15} className="spin" /> : <ShoppingCart size={15} />}
        {adding ? ' Adding…' : ' Add to cart'}
      </button>
    </header>
  );
}
