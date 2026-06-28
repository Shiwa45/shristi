import { useState, useEffect, useRef } from 'react';
import { Search, Square, Circle, Triangle, Minus, Type, Upload, Eye, EyeOff, Lock, Unlock, Trash2, ChevronUp, ChevronDown, Image as ImageIcon, Group, Ungroup, Egg, Pentagon, Hexagon, Octagon, Star, Heart, MoveUpRight, MessageCircle, QrCode, Pencil, Folder } from 'lucide-react';
import { useEditor } from '../store/editorStore';
import { api } from '../services/api';
import { fromPx } from '../config/printConfig';
import QRCode from 'qrcode';

export default function LeftPanel() {
  const activePanel = useEditor((s) => s.activePanel);
  return (
    <aside className="leftpanel">
      {activePanel === 'templates' && <Templates />}
      {activePanel === 'elements' && <Elements />}
      {activePanel === 'text' && <TextTab />}
      {activePanel === 'images' && <Photos />}
      {activePanel === 'uploads' && <Uploads />}
      {activePanel === 'mydesigns' && <MyDesigns />}
      {activePanel === 'layers' && <LayersTab />}
      {activePanel === 'stickers' && <Stickers />}
    </aside>
  );
}

// ---------------- TEMPLATES ----------------
function Templates() {
  const engine = useEditor((s) => s.engine);
  const studioTemplates = useEditor((s) => s.studioTemplates);
  const productConfig = useEditor((s) => s.productConfig);
  const activeSide = useEditor((s) => s.activeSide);
  const [loading, setLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');

  // Derive unique categories from Django templates
  const categories = ['all', ...new Set(studioTemplates.map((t) => t.category).filter(Boolean))];

  // Filter by category, then show only generic (no side) + matching-side templates
  const byCat = activeCategory === 'all'
    ? studioTemplates
    : studioTemplates.filter((t) => t.category === activeCategory);
  const visible = byCat.filter((t) => !t.side || t.side === activeSide);

  // Load a Django template onto the canvas
  const loadDjangoTemplate = async (t) => {
    if (!engine) return;
    setLoading(true);
    try {
      if (t.type === 'json' && t.template_data) {
        // Fabric.js JSON — load directly
        await engine.loadFabricJSON(t.template_data);
      } else if (t.type === 'svg' && t.svg_url) {
        // SVG file — fetch content then load
        const res = await fetch(t.svg_url);
        if (!res.ok) throw new Error(`SVG fetch failed: ${res.status}`);
        const svgText = await res.text();
        engine.loadSvgTemplate(svgText);
      } else {
        loadColorStarter('#1d2b4f');
      }
    } catch (e) {
      console.error('[loadTemplate]', e);
    } finally {
      setLoading(false);
    }
  };

  // Generate and load a plain colour SVG as a canvas starter
  const loadColorStarter = (accent) => {
    if (!engine) return;
    const w = engine.docW, h = engine.docH;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
      <rect width="${w}" height="${h}" fill="${accent}"/>
      <rect x="${w*0.08}" y="${h*0.55}" width="${w*0.84}" height="2" fill="#ffffff" opacity="0.6"/>
      <text x="${w*0.08}" y="${h*0.42}" font-family="sans-serif" font-size="${h*0.10}" font-weight="700" fill="#ffffff">Your Name</text>
      <text x="${w*0.08}" y="${h*0.68}" font-family="sans-serif" font-size="${h*0.05}" fill="#ffffff" opacity="0.85">Title / Company</text>
    </svg>`;
    engine.loadSvgTemplate(svg);
  };

  const palettes = ['#1d2b4f', '#0f5132', '#7b1d3a', '#3a2d6b', '#b5651d', '#1a1a1a'];

  return (
    <>
      <div className="panel-head">
        <h2>Templates</h2>
        <p>
          {productConfig
            ? `${studioTemplates.length} template${studioTemplates.length !== 1 ? 's' : ''} for ${productConfig.name}`
            : 'Fully editable layouts'}
        </p>
      </div>
      <div className="panel-body">

        {/* Category filter pills — only shown when Django templates are present */}
        {studioTemplates.length > 0 && categories.length > 2 && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
            {categories.map((c) => (
              <button
                key={c}
                onClick={() => setActiveCategory(c)}
                style={{
                  fontSize: 11, padding: '3px 10px', borderRadius: 20, border: '1px solid var(--border)',
                  background: activeCategory === c ? 'var(--accent)' : 'transparent',
                  color: activeCategory === c ? '#fff' : 'var(--text-2)',
                  cursor: 'pointer',
                }}
              >
                {c === 'all' ? 'All' : c}
              </button>
            ))}
          </div>
        )}

        {loading && <p style={{ fontSize: 12, color: 'var(--text-2)' }}>Loading template…</p>}

        {/* Django templates grid */}
        <div className="grid2">
          {visible.map((t) => (
            <div key={t.id} className="tmpl" onClick={() => loadDjangoTemplate(t)}
              title={t.description || t.name}
              style={{ position: 'relative', marginBottom: 0 }}>
              <div className="thumb" style={{ background: '#f0f0f0', overflow: 'hidden', aspectRatio: '1.4' }}>
                {t.thumbnail
                  ? <img src={t.thumbnail} alt={t.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
                  : <div style={{ width: '100%', height: '100%', background: '#1d2b4f',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: '#fff', fontSize: 10, textAlign: 'center', padding: 4 }}>
                      {t.name}
                    </div>
                }
                {t.is_featured && (
                  <span style={{ position: 'absolute', top: 4, right: 4, background: '#f5a623',
                    color: '#fff', fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 10 }}>
                    ★
                  </span>
                )}
              </div>
              <div className="meta">{t.name}</div>
            </div>
          ))}
        </div>

        {/* Fallback quick starters when no Django templates */}
        {studioTemplates.length === 0 && (
          <>
            <div className="divider" />
            <label style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 8, display: 'block' }}>
              Quick colour starters
            </label>
            <div className="grid3">
              {palettes.map((c) => (
                <div key={c} className="tile" style={{ background: c }}
                  onClick={() => loadColorStarter(c)} />
              ))}
            </div>
            <p style={{ fontSize: 11, color: 'var(--text-2)', marginTop: 14, lineHeight: 1.5 }}>
              Add templates for this product in the Django admin and they will appear here automatically.
            </p>
          </>
        )}

      </div>
    </>
  );
}

// ---------------- ELEMENTS (shapes + graphics) ----------------
function Elements() {
  const engine = useEditor((s) => s.engine);
  const [graphics, setGraphics] = useState([]);
  useEffect(() => { api.getGraphics().then(setGraphics); }, []);

  const shapes = [
    { icon: Square, fn: () => engine?.addRect() },
    { icon: Circle, fn: () => engine?.addCircle() },
    { icon: Triangle, fn: () => engine?.addTriangle() },
    { icon: Minus, fn: () => engine?.addLine() },
    { icon: Egg, fn: () => engine?.addEllipse() },
    { icon: Pentagon, fn: () => engine?.addPolygon(5) },
    { icon: Hexagon, fn: () => engine?.addPolygon(6) },
    { icon: Octagon, fn: () => engine?.addPolygon(8) },
    { icon: Star, fn: () => engine?.addStar(5) },
    { icon: Heart, fn: () => engine?.addHeart() },
    { icon: MoveUpRight, fn: () => engine?.addArrow() },
    { icon: MessageCircle, fn: () => engine?.addSpeechBubble() },
  ];

  return (
    <>
      <div className="panel-head"><h2>Elements</h2><p>Shapes & vector graphics</p></div>
      <div className="panel-body">
        <label style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 8, display: 'block' }}>Basic shapes</label>
        <div className="grid3">
          {shapes.map(({ icon: Icon, fn }, i) => (
            <button key={i} className="tile shape" onClick={fn}><Icon size={26} strokeWidth={1.6} /></button>
          ))}
        </div>
        <div className="divider" />
        <label style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 8, display: 'block' }}>Graphics</label>
        <div className="grid3">
          {graphics.map((g) => (
            <button key={g.id} className="tile shape" onClick={() => engine?.addSvgString(g.svg)}>
              <span className="clip" style={{ display: 'grid', placeItems: 'center', width: '56%', height: '56%' }}
                dangerouslySetInnerHTML={{ __html: g.svg }} />
            </button>
          ))}
        </div>

        <div className="divider" />
        <QRGenerator engine={engine} />

        <div className="divider" />
        <FreeDrawControls engine={engine} />
      </div>
    </>
  );
}

// ---------------- QR GENERATOR ----------------
function QRGenerator({ engine }) {
  const [val, setVal] = useState('https://');
  const [color, setColor] = useState('#000000');
  const add = async () => {
    if (!val.trim()) return;
    const url = await QRCode.toDataURL(val, { margin: 1, width: 600, color: { dark: color, light: '#00000000' } });
    engine?.addQRCode(url);
  };
  return (
    <div>
      <label style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}><QrCode size={13} /> QR code</label>
      <input className="input" style={{ marginBottom: 6 }} value={val} onChange={(e) => setVal(e.target.value)} placeholder="URL or text" />
      <div className="row" style={{ alignItems: 'center' }}>
        <div className="color-swatch" style={{ background: color, flex: '0 0 34px' }}>
          <input type="color" value={color} onChange={(e) => setColor(e.target.value)} />
        </div>
        <button className="btn primary" style={{ justifyContent: 'center' }} onClick={add}>Generate</button>
      </div>
    </div>
  );
}

// ---------------- FREE DRAW ----------------
function FreeDrawControls({ engine }) {
  const [on, setOn] = useState(false);
  const [color, setColor] = useState('#1a1a1a');
  const [width, setWidth] = useState(6);
  const toggle = () => { const n = !on; setOn(n); engine?.setDrawing(n, { color, width }); };
  useEffect(() => { if (on) engine?.setBrush({ color, width }); }, [color, width]); // eslint-disable-line
  return (
    <div>
      <label style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}><Pencil size={13} /> Free draw</label>
      <button className={`btn ${on ? 'primary' : ''}`} style={{ width: '100%', justifyContent: 'center', marginBottom: 8 }} onClick={toggle}>
        {on ? 'Drawing on — click to stop' : 'Start drawing'}
      </button>
      {on && (
        <>
          <div className="row" style={{ alignItems: 'center', marginBottom: 6 }}>
            <div className="color-swatch" style={{ flex: '0 0 34px', background: color }}>
              <input type="color" value={color} onChange={(e) => setColor(e.target.value)} />
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-2)' }}>Brush {width}px</span>
          </div>
          <input className="slider" type="range" min="1" max="40" value={width} onChange={(e) => setWidth(+e.target.value)} />
        </>
      )}
    </div>
  );
}

// ---------------- TEXT ----------------
function TextTab() {
  const engine = useEditor((s) => s.engine);
  const presets = [
    { label: 'Add a heading', size: 120, weight: 700, style: { fontSize: 24, fontWeight: 700 } },
    { label: 'Add a subheading', size: 72, weight: 600, style: { fontSize: 18, fontWeight: 600 } },
    { label: 'Add body text', size: 42, weight: 400, style: { fontSize: 14, fontWeight: 400 } },
  ];
  return (
    <>
      <div className="panel-head"><h2>Text</h2><p>Click to add editable text</p></div>
      <div className="panel-body">
        {presets.map((p) => (
          <button key={p.label} className="txt-preset" style={p.style}
            onClick={() => engine?.addText(p.label, { fontSize: p.size, fontWeight: p.weight })}>
            {p.label}
          </button>
        ))}
      </div>
    </>
  );
}

// ---------------- PHOTOS (stock search) ----------------
function Photos() {
  const engine = useEditor((s) => s.engine);
  const [q, setQ] = useState('abstract');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const run = async (query) => {
    setLoading(true);
    const r = await api.searchImages(query || q);
    setResults(r); setLoading(false);
  };
  useEffect(() => { run('abstract'); }, []);

  return (
    <>
      <div className="panel-head"><h2>Photos</h2><p>Stock images via your API</p></div>
      <div className="panel-body">
        <div className="search">
          <Search size={15} color="var(--text-2)" />
          <input value={q} onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && run()} placeholder="Search photos..." />
        </div>
        {loading ? <p style={{ color: 'var(--text-2)', fontSize: 12 }}>Loading…</p> : (
          <div className="grid2">
            {results.map((img) => (
              <div key={img.id} className="tile" onClick={() => engine?.addImageFromUrl(img.full)}>
                <img src={img.thumb} alt="" loading="lazy" />
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

// ---------------- UPLOADS ----------------
function Uploads() {
  const engine = useEditor((s) => s.engine);
  const [uploads, setUploads] = useState([]);
  const inputRef = useRef();

  const handleFiles = async (files) => {
    for (const f of files) {
      const { url } = await api.uploadImage(f);
      setUploads((u) => [{ id: Math.random().toString(36).slice(2), url }, ...u]);
    }
  };

  return (
    <>
      <div className="panel-head"><h2>Uploads</h2><p>Your images & logos</p></div>
      <div className="panel-body">
        <div className="upload-zone" onClick={() => inputRef.current.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); handleFiles([...e.dataTransfer.files]); }}>
          <Upload size={22} style={{ marginBottom: 8 }} />
          <div style={{ fontSize: 12.5 }}>Drop images or click to upload</div>
        </div>
        <input ref={inputRef} type="file" accept="image/*,.svg" multiple hidden
          onChange={(e) => handleFiles([...e.target.files])} />
        <div className="grid2">
          {uploads.map((u) => (
            <div key={u.id} className="tile" onClick={() => {
              u.url.includes('svg') || u.url.startsWith('data:image/svg')
                ? fetch(u.url).then(r => r.text()).then(s => engine?.addSvgString(s)).catch(() => engine?.addImageFromUrl(u.url))
                : engine?.addImageFromUrl(u.url);
            }}>
              <img src={u.url} alt="" />
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

// ---------------- LAYERS ----------------
function LayersTab() {
  const engine = useEditor((s) => s.engine);
  const layers = useEditor((s) => s.layers);
  const [editing, setEditing] = useState(null);
  const [name, setName] = useState('');

  const iconFor = (type) => {
    if (type?.includes('text')) return <Type size={15} />;
    if (type === 'image') return <ImageIcon size={15} />;
    if (type === 'group') return <Group size={15} />;
    if (type === 'circle') return <Circle size={15} />;
    if (type === 'triangle') return <Triangle size={15} />;
    return <Square size={15} />;
  };

  return (
    <>
      <div className="panel-head">
        <h2>Layers</h2><p>{layers.length} object{layers.length !== 1 ? 's' : ''}</p>
      </div>
      <div className="panel-body">
        {layers.length === 0 && <p style={{ color: 'var(--text-2)', fontSize: 12 }}>Canvas is empty.</p>}
        {layers.map((l) => (
          <div key={l.id} className={`layer ${l.selected ? 'selected' : ''}`}
            onClick={() => engine?.selectById(l.id)}>
            <span className="l-icon">{iconFor(l.type)}</span>
            <span className="l-name" onDoubleClick={() => { setEditing(l.id); setName(l.name); }}>
              {editing === l.id ? (
                <input autoFocus value={name} onChange={(e) => setName(e.target.value)}
                  onBlur={() => { engine.renameLayer(l.id, name); setEditing(null); }}
                  onKeyDown={(e) => { if (e.key === 'Enter') { engine.renameLayer(l.id, name); setEditing(null); } }}
                  onClick={(e) => e.stopPropagation()} />
              ) : l.name}
            </span>
            <button className="l-act" title="Up" onClick={(e) => { e.stopPropagation(); engine.reorderLayer(l.id, 'up'); }}><ChevronUp size={14} /></button>
            <button className="l-act" title="Down" onClick={(e) => { e.stopPropagation(); engine.reorderLayer(l.id, 'down'); }}><ChevronDown size={14} /></button>
            <button className="l-act" title="Visibility" onClick={(e) => { e.stopPropagation(); engine.setVisible(l.ref, !l.visible); }}>
              {l.visible ? <Eye size={14} /> : <EyeOff size={14} />}
            </button>
            <button className="l-act" title="Lock" onClick={(e) => { e.stopPropagation(); engine.selectById(l.id); engine.toggleLock(); }}>
              {l.locked ? <Lock size={14} /> : <Unlock size={14} />}
            </button>
          </div>
        ))}
      </div>
    </>
  );
}

// ---------------- STICKERS ----------------
const STICKER_CATEGORIES = [
  { name: 'animals',        count: 10,  type: 'png' },
  { name: 'beach',          count: 22,  type: 'svg' },
  { name: 'bubbles',        count: 105, type: 'png' },
  { name: 'clouds',         count: 15,  type: 'png' },
  { name: 'doodles',        count: 100, type: 'svg' },
  { name: 'landmarks',      count: 100, type: 'svg' },
  { name: 'stars',          count: 6,   type: 'png' },
  { name: 'transportation', count: 22,  type: 'svg' },
];

function Stickers() {
  const engine = useEditor((s) => s.engine);
  const [activeCategory, setActiveCategory] = useState('animals');

  const cat = STICKER_CATEGORIES.find((c) => c.name === activeCategory);
  const stickers = cat
    ? Array.from({ length: cat.count }, (_, i) => ({
        id: i + 1,
        url: `/assets/stickers/${cat.name}/${i + 1}.${cat.type}`,
      }))
    : [];

  return (
    <>
      <div className="panel-head">
        <h2>Stickers</h2>
        <p>{cat ? cat.count : 0} stickers · click to add</p>
      </div>
      <div className="panel-body">
        {/* Category pills */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
          {STICKER_CATEGORIES.map((c) => (
            <button
              key={c.name}
              onClick={() => setActiveCategory(c.name)}
              style={{
                fontSize: 11, padding: '3px 10px', borderRadius: 20,
                border: '1px solid var(--border)',
                background: activeCategory === c.name ? 'var(--accent)' : 'transparent',
                color: activeCategory === c.name ? '#fff' : 'var(--text-2)',
                cursor: 'pointer', textTransform: 'capitalize',
              }}
            >
              {c.name}
            </button>
          ))}
        </div>

        {/* Sticker grid */}
        <div className="grid3">
          {stickers.map(({ id, url }) => (
            <button
              key={id}
              className="tile"
              onClick={() => engine?.addStickerFromUrl(url)}
              title={`${activeCategory} ${id}`}
              style={{ padding: 4, background: 'var(--surface-2)' }}
            >
              <img
                src={url}
                alt=""
                loading="lazy"
                style={{ width: '100%', height: '100%', objectFit: 'contain', pointerEvents: 'none' }}
              />
            </button>
          ))}
        </div>
      </div>
    </>
  );
}

// ---------------- MY DESIGNS (saved gallery) ----------------
function MyDesigns() {
  const engine = useEditor((s) => s.engine);
  const [designs, setDesigns] = useState([]);
  const [name, setName] = useState('');

  const refresh = () => api.listMyDesigns().then(setDesigns);
  useEffect(() => { refresh(); }, []);

  const save = async () => {
    if (!engine) return;
    const thumb = engine.exportPNG({ includeBleed: false, multiplier: 0.25 });
    await api.saveNamedDesign({ name: name || 'Untitled', thumb, design: engine.serialize() });
    setName(''); refresh();
  };
  const load = async (d) => {
    if (!engine || !d.design) return;
    const side = d.design.sides?.[d.design.activeSide];
    if (side) await engine.loadFabricJSON(side);
    if (d.design.background) engine.setBackgroundColor(d.design.background);
  };
  const del = async (id) => { await api.deleteMyDesign(id); refresh(); };

  return (
    <>
      <div className="panel-head"><h2>Saved designs</h2><p>Save & reload your work</p></div>
      <div className="panel-body">
        <div className="row" style={{ marginBottom: 12 }}>
          <input className="input" placeholder="Design name" value={name} onChange={(e) => setName(e.target.value)} />
          <button className="btn primary" style={{ flex: '0 0 auto', justifyContent: 'center' }} onClick={save}>Save</button>
        </div>
        {designs.length === 0 && <p style={{ color: 'var(--text-2)', fontSize: 12 }}>No saved designs yet.</p>}
        <div className="grid2">
          {designs.map((d) => (
            <div key={d.id} className="tmpl" style={{ marginBottom: 0 }}>
              <div className="thumb" style={{ background: '#fff', aspectRatio: '1.3' }} onClick={() => load(d)}>
                {d.thumb ? <img src={d.thumb} alt="" style={{ width: '100%', height: '100%', objectFit: 'contain' }} /> : null}
              </div>
              <div className="meta" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.name}</span>
                <button className="l-act" onClick={() => del(d.id)}><Trash2 size={13} /></button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
