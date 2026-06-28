import { X } from 'lucide-react';
import { useEditor } from '../store/editorStore';
import { PRODUCT_PRESETS } from '../config/printConfig';
import { useState } from 'react';

function Modal({ title, onClose, children, footer }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>{title}</h3>
          <button className="iconbtn" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  );
}

export function ProductModal({ onClose }) {
  const { product, setProduct } = useEditor();
  const [custom, setCustom] = useState({ w: 100, h: 100, unit: 'mm', bleed: 3, safe: 5 });

  const pick = (p) => { setProduct(p); onClose(); };
  const applyCustom = () => {
    setProduct({
      id: 'custom', category: 'Custom', name: `Custom ${custom.w}×${custom.h}${custom.unit}`,
      width: +custom.w, height: +custom.h, unit: custom.unit,
      bleed: +custom.bleed, safe: +custom.safe, sides: ['front', 'back'],
    });
    onClose();
  };

  return (
    <Modal title="Choose product" onClose={onClose}>
      {PRODUCT_PRESETS.filter((p) => p.id !== 'custom').map((p) => (
        <div key={p.id} className={`product-card ${product.id === p.id ? 'active' : ''}`} onClick={() => pick(p)}>
          <div>
            <div className="pc-cat">{p.category}</div>
            <div style={{ fontWeight: 500, marginTop: 2 }}>{p.name}</div>
          </div>
          <div className="pc-dim">{p.width}×{p.height} {p.unit}</div>
        </div>
      ))}
      <div className="divider" />
      <div className="pc-cat" style={{ color: 'var(--accent-2)', marginBottom: 10 }}>Custom size</div>
      <div className="row">
        <div className="field"><span>Width</span><input className="input" type="number" value={custom.w} onChange={(e) => setCustom({ ...custom, w: e.target.value })} /></div>
        <div className="field"><span>Height</span><input className="input" type="number" value={custom.h} onChange={(e) => setCustom({ ...custom, h: e.target.value })} /></div>
        <div className="field"><span>Unit</span>
          <select className="input" value={custom.unit} onChange={(e) => setCustom({ ...custom, unit: e.target.value })}>
            <option value="mm">mm</option><option value="cm">cm</option><option value="in">in</option><option value="px">px</option>
          </select>
        </div>
      </div>
      <div className="row">
        <div className="field"><span>Bleed (mm)</span><input className="input" type="number" value={custom.bleed} onChange={(e) => setCustom({ ...custom, bleed: e.target.value })} /></div>
        <div className="field"><span>Safe (mm)</span><input className="input" type="number" value={custom.safe} onChange={(e) => setCustom({ ...custom, safe: e.target.value })} /></div>
      </div>
      <button className="btn primary" style={{ width: '100%', justifyContent: 'center', marginTop: 6 }} onClick={applyCustom}>Apply custom size</button>
    </Modal>
  );
}

const SHORTCUTS = [
  ['Undo / Redo', 'Ctrl+Z / Ctrl+Shift+Z'],
  ['Duplicate', 'Ctrl+D'],
  ['Copy / Paste', 'Ctrl+C / Ctrl+V'],
  ['Group / Ungroup', 'Ctrl+G / Ctrl+Shift+G'],
  ['Bring forward / back', 'Ctrl+] / Ctrl+['],
  ['Delete', 'Del / Backspace'],
  ['Nudge', 'Arrow keys'],
  ['Nudge ×10', 'Shift + Arrows'],
  ['Lock / unlock', 'L'],
  ['Zoom in / out', 'Ctrl+= / Ctrl+−'],
  ['Fit to screen', 'Ctrl+0'],
  ['Save', 'Ctrl+S'],
  ['Deselect', 'Esc'],
];

export function ShortcutsModal({ onClose }) {
  return (
    <Modal title="Keyboard shortcuts" onClose={onClose}>
      {SHORTCUTS.map(([label, keys]) => (
        <div key={label} className="shortcut-row">
          <span>{label}</span><span className="kbd">{keys}</span>
        </div>
      ))}
    </Modal>
  );
}

export function ExportModal({ onClose }) {
  const engine = useEditor((s) => s.engine);
  const [includeBleed, setIncludeBleed] = useState(true);
  const [scale, setScale] = useState(2);

  const download = (dataUrl, name) => {
    const a = document.createElement('a');
    a.href = dataUrl; a.download = name; a.click();
  };
  const pngExport = () => { download(engine.exportPNG({ includeBleed, multiplier: scale }), 'design.png'); onClose(); };
  const svgExport = () => {
    const svg = engine.exportSVG();
    download('data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg), 'design.svg');
    onClose();
  };
  const jsonExport = () => {
    download('data:application/json,' + encodeURIComponent(JSON.stringify(engine.serialize())), 'design.json');
    onClose();
  };

  return (
    <Modal title="Export design" onClose={onClose}
      footer={<>
        <button className="btn" onClick={svgExport}>SVG</button>
        <button className="btn" onClick={jsonExport}>JSON</button>
        <button className="btn primary" onClick={pngExport}>Download PNG</button>
      </>}>
      <div className="field">
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
          <input type="checkbox" checked={includeBleed} onChange={(e) => setIncludeBleed(e.target.checked)} />
          Include bleed area (recommended for print shops)
        </label>
      </div>
      <div className="field" style={{ marginTop: 14 }}>
        <span>Resolution scale: {scale}× ({Math.round(300 * scale)} DPI effective)</span>
        <input className="slider" type="range" min="1" max="4" step="1" value={scale} onChange={(e) => setScale(+e.target.value)} />
      </div>
      <p style={{ fontSize: 11.5, color: 'var(--text-2)', marginTop: 14, lineHeight: 1.5 }}>
        PNG renders at print resolution. SVG keeps vectors editable. JSON is the full editable design state for re-loading later.
      </p>
    </Modal>
  );
}

export function PreflightModal({ onClose }) {
  const engine = useEditor((s) => s.engine);
  const issues = engine ? engine.preflight() : [];
  const ok = issues.length === 0;
  return (
    <Modal title="Print preflight check" onClose={onClose}
      footer={<button className="btn primary" onClick={onClose}>Close</button>}>
      {ok ? (
        <p style={{ color: 'var(--safe)', fontSize: 13 }}>✓ All clear — nothing outside the safe area and image resolution looks good for print.</p>
      ) : (
        <>
          <p style={{ fontSize: 12.5, color: 'var(--text-1)', marginBottom: 12 }}>{issues.length} potential issue{issues.length > 1 ? 's' : ''} found:</p>
          {issues.map((i, idx) => (
            <div key={idx} className="shortcut-row">
              <span>{i.type === 'low-res' ? `Low resolution: ${i.name}` : `Outside safe area: ${i.name}`}</span>
              <span className="kbd" style={{ color: i.type === 'low-res' ? 'var(--danger)' : 'var(--warn)' }}>
                {i.type === 'low-res' ? `~${i.dpi} DPI` : 'move inward'}
              </span>
            </div>
          ))}
          <p style={{ fontSize: 11.5, color: 'var(--text-2)', marginTop: 14, lineHeight: 1.5 }}>
            Keep important content inside the green safe line. Images below ~150 DPI may look blurry when printed.
          </p>
        </>
      )}
    </Modal>
  );
}
