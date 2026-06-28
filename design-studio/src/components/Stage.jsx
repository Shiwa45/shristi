import { useEffect, useRef, useState } from 'react';
import { ZoomIn, ZoomOut, Maximize, Grid3x3, Ruler, Magnet } from 'lucide-react';
import { CanvasEngine } from '../canvas/CanvasEngine';
import { useEditor } from '../store/editorStore';
import { GUIDE_COLORS } from '../config/printConfig';

export default function Stage() {
  const canvasRef = useRef(null);
  const [bg, setBg] = useState('#ffffff');
  const {
    engine, setEngine, product, sides, activeSide, setActiveSide,
    zoom, update, showBleed, showSafe, showTrim, showGrid, snapToGuides, toggleGuide,
  } = useEditor();

  // init engine once
  useEffect(() => {
    if (!canvasRef.current) return;
    const eng = new CanvasEngine(canvasRef.current, {
      onChange: () => {
        update({
          layers: eng.getLayers(),
          canUndo: eng.canUndo(),
          canRedo: eng.canRedo(),
          activeObjectProps: serializeActive(eng.getActive()),
        });
      },
    });
    eng.setSnap(true);
    eng.applyProduct(product);
    setEngine(eng);
    update({ zoom: eng.canvas.getZoom() });
    return () => eng.dispose();
    // eslint-disable-next-line
  }, []);

  // refit on window resize
  useEffect(() => {
    const onResize = () => { if (engine) { const z = engine.fitToScreen(); update({ zoom: z }); } };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [engine]);

  // sync guide flags
  useEffect(() => {
    engine?.setGuideFlags({ bleed: showBleed, safe: showSafe, trim: showTrim, grid: showGrid });
  }, [engine, showBleed, showSafe, showTrim, showGrid]);

  useEffect(() => { engine?.setSnap(snapToGuides); }, [engine, snapToGuides]);

  const setZoom = (z) => { engine?.setZoom(z); update({ zoom: z }); };
  const fit = () => { const z = engine?.fitToScreen(); update({ zoom: z }); };

  const activeIdx = sides.indexOf(activeSide);

  return (
    <main className="stage">
      <div className="stage-bar">
        <div className="spacer" style={{ flex: 1 }} />
        <label className="guide-chip on" style={{ cursor: 'pointer', gap: 6 }} title="Background color">
          <span className="dot" style={{ background: bg, border: '1px solid var(--line)' }} />
          BG
          <input type="color" value={bg} style={{ width: 0, height: 0, opacity: 0, position: 'absolute' }}
            onChange={(e) => { setBg(e.target.value); engine?.setBackgroundColor(e.target.value); }} />
        </label>
        <div className="guide-toggles">
          <Chip on={showBleed} color={GUIDE_COLORS.bleed} label="Bleed" onClick={() => toggleGuide('showBleed')} />
          <Chip on={showTrim} color={GUIDE_COLORS.trim} label="Trim" onClick={() => toggleGuide('showTrim')} />
          <Chip on={showSafe} color={GUIDE_COLORS.safe} label="Safe" onClick={() => toggleGuide('showSafe')} />
          <button className={`guide-chip ${showGrid ? 'on' : ''}`} onClick={() => toggleGuide('showGrid')}><Grid3x3 size={13} /> Grid</button>
          <button className={`guide-chip ${snapToGuides ? 'on' : ''}`} onClick={() => toggleGuide('snapToGuides')}><Magnet size={13} /> Snap</button>
        </div>
      </div>

      <div className="canvas-wrap">
        <div className="canvas-shell">
          <canvas ref={canvasRef} />
        </div>

        {/* Bottom bar: zoom left + side pagination centre-right */}
        <div className="zoombar">
          <button className="iconbtn" onClick={() => setZoom(Math.max(zoom / 1.15, 0.05))}><ZoomOut size={16} /></button>
          <span className="z-val">{Math.round(zoom * 100)}%</span>
          <button className="iconbtn" onClick={() => setZoom(Math.min(zoom * 1.15, 4))}><ZoomIn size={16} /></button>
          <button className="iconbtn" title="Fit (Ctrl+0)" onClick={fit}><Maximize size={15} /></button>

          {sides.length > 1 && (
            <div className="side-pager">
              <button
                className="side-pager-btn"
                disabled={activeIdx === 0}
                onClick={() => setActiveSide(sides[activeIdx - 1])}
              >‹</button>
              {sides.map((s, i) => (
                <button
                  key={s}
                  className={`side-pager-dot ${activeSide === s ? 'active' : ''}`}
                  onClick={() => setActiveSide(s)}
                  title={s.charAt(0).toUpperCase() + s.slice(1)}
                >
                  <span className="side-pager-num">{i + 1}</span>
                  <span className="side-pager-label">{s.charAt(0).toUpperCase() + s.slice(1)}</span>
                </button>
              ))}
              <button
                className="side-pager-btn"
                disabled={activeIdx === sides.length - 1}
                onClick={() => setActiveSide(sides[activeIdx + 1])}
              >›</button>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

function Chip({ on, color, label, onClick }) {
  return (
    <button className={`guide-chip ${on ? 'on' : ''}`} onClick={onClick}>
      <span className="dot" style={{ background: on ? color : 'var(--text-2)' }} /> {label}
    </button>
  );
}

function serializeActive(o) {
  if (!o) return null;
  return {
    type: o.type, left: o.left, top: o.top, width: o.width, height: o.height,
    scaleX: o.scaleX, scaleY: o.scaleY, angle: o.angle, fill: o.fill,
    stroke: o.stroke, strokeWidth: o.strokeWidth, opacity: o.opacity,
    rx: o.rx, fontFamily: o.fontFamily, fontSize: o.fontSize, fontWeight: o.fontWeight,
    fontStyle: o.fontStyle, underline: o.underline, textAlign: o.textAlign,
    charSpacing: o.charSpacing, lineHeight: o.lineHeight,
    shadow: o.shadow, __curve: o.__curve,
  };
}
