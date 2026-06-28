import { useEditor } from '../store/editorStore';
import { api } from '../services/api';
import { useEffect, useState } from 'react';
import {
  AlignLeft, AlignCenter, AlignRight, AlignJustify, Bold, Italic, Underline,
  AlignStartVertical, AlignCenterVertical, AlignEndVertical,
  AlignStartHorizontal, AlignCenterHorizontal, AlignEndHorizontal,
  FlipHorizontal, FlipVertical,
} from 'lucide-react';

export default function RightPanel() {
  const engine = useEditor((s) => s.engine);
  const props = useEditor((s) => s.activeObjectProps);
  const [fonts, setFonts] = useState([]);

  useEffect(() => {
    api.getFonts().then((f) => {
      setFonts(f);
      f.forEach((font) => {
        if (font.url && !document.querySelector(`link[href="${font.url}"]`)) {
          const link = document.createElement('link');
          link.rel = 'stylesheet'; link.href = font.url;
          document.head.appendChild(link);
        }
      });
    });
  }, []);

  // Nothing selected → render nothing so the propbar row collapses and the canvas gets full space.
  if (!engine || !props) return null;

  const up = (patch) => engine.updateActive(patch);
  const isText = props.type?.includes('text');
  const hasFill = props.fill !== undefined;

  return (
    <div className="propbar">
      {/* Arrange */}
      <div className="pb-group">
        <div className="btn-group">
          <button title="Align left" onClick={() => engine.align('left')}><AlignStartVertical size={15} /></button>
          <button title="Center H" onClick={() => engine.align('centerH')}><AlignCenterVertical size={15} /></button>
          <button title="Align right" onClick={() => engine.align('right')}><AlignEndVertical size={15} /></button>
          <button title="Align top" onClick={() => engine.align('top')}><AlignStartHorizontal size={15} /></button>
          <button title="Center V" onClick={() => engine.align('centerV')}><AlignCenterHorizontal size={15} /></button>
          <button title="Align bottom" onClick={() => engine.align('bottom')}><AlignEndHorizontal size={15} /></button>
        </div>
        <div className="btn-group">
          <button title="Flip H" onClick={() => engine.flip('x')}><FlipHorizontal size={15} /></button>
          <button title="Flip V" onClick={() => engine.flip('y')}><FlipVertical size={15} /></button>
        </div>
      </div>

      <span className="pb-sep" />

      {/* Position & size */}
      <div className="pb-group">
        <div className="pb-field"><span>X</span>
          <input className="pb-input" type="number" value={Math.round(props.left)} onChange={(e) => up({ left: +e.target.value })} /></div>
        <div className="pb-field"><span>Y</span>
          <input className="pb-input" type="number" value={Math.round(props.top)} onChange={(e) => up({ top: +e.target.value })} /></div>
        <div className="pb-field"><span>W</span>
          <input className="pb-input" type="number" value={Math.round(props.width * (props.scaleX || 1))}
            onChange={(e) => up({ scaleX: +e.target.value / props.width })} /></div>
        <div className="pb-field"><span>H</span>
          <input className="pb-input" type="number" value={Math.round(props.height * (props.scaleY || 1))}
            onChange={(e) => up({ scaleY: +e.target.value / props.height })} /></div>
        <div className="pb-field" title="Rotation"><span>∠</span>
          <input className="slider pb-slider" type="range" min="0" max="360" value={props.angle || 0}
            onChange={(e) => up({ angle: +e.target.value })} /></div>
      </div>

      {/* Text controls */}
      {isText && (
        <>
          <span className="pb-sep" />
          <div className="pb-group">
            <select className="pb-input wide" value={props.fontFamily} onChange={(e) => up({ fontFamily: e.target.value })}>
              {fonts.map((f) => <option key={f.family} value={f.family} style={{ fontFamily: f.family }}>{f.family}</option>)}
            </select>
            <div className="pb-field"><span>Size</span>
              <input className="pb-input" type="number" value={Math.round(props.fontSize)} onChange={(e) => up({ fontSize: +e.target.value })} /></div>
            <div className="pb-field"><span>Spc</span>
              <input className="pb-input" type="number" value={props.charSpacing || 0} onChange={(e) => up({ charSpacing: +e.target.value })} /></div>
            <div className="btn-group">
              <button className={props.fontWeight >= 700 ? 'active' : ''} onClick={() => up({ fontWeight: props.fontWeight >= 700 ? 400 : 700 })}><Bold size={15} /></button>
              <button className={props.fontStyle === 'italic' ? 'active' : ''} onClick={() => up({ fontStyle: props.fontStyle === 'italic' ? 'normal' : 'italic' })}><Italic size={15} /></button>
              <button className={props.underline ? 'active' : ''} onClick={() => up({ underline: !props.underline })}><Underline size={15} /></button>
            </div>
            <div className="btn-group">
              <button className={props.textAlign === 'left' ? 'active' : ''} onClick={() => up({ textAlign: 'left' })}><AlignLeft size={15} /></button>
              <button className={props.textAlign === 'center' ? 'active' : ''} onClick={() => up({ textAlign: 'center' })}><AlignCenter size={15} /></button>
              <button className={props.textAlign === 'right' ? 'active' : ''} onClick={() => up({ textAlign: 'right' })}><AlignRight size={15} /></button>
              <button className={props.textAlign === 'justify' ? 'active' : ''} onClick={() => up({ textAlign: 'justify' })}><AlignJustify size={15} /></button>
            </div>
            <div className="pb-field" title="Line height"><span>LH</span>
              <input className="slider pb-slider" type="range" min="0.5" max="3" step="0.1" value={props.lineHeight || 1.16}
                onChange={(e) => up({ lineHeight: +e.target.value })} /></div>
            <div className="pb-field" title="Curve"><span>Curve</span>
              <input className="slider pb-slider" type="range" min="-100" max="100" value={props.__curve || 0}
                onChange={(e) => engine.setTextCurve(+e.target.value)} /></div>
          </div>
        </>
      )}

      {/* Fill */}
      {hasFill && (
        <>
          <span className="pb-sep" />
          <div className="pb-group">
            <span className="pb-label">Fill</span>
            <div className="color-swatch" style={{ background: props.fill || '#000' }}>
              <input type="color" value={toHex(props.fill)} onChange={(e) => up({ fill: e.target.value })} />
            </div>
            <input className="pb-input wide" value={props.fill || ''} onChange={(e) => up({ fill: e.target.value })} />
          </div>
        </>
      )}

      {/* Stroke */}
      <span className="pb-sep" />
      <div className="pb-group">
        <span className="pb-label">Stroke</span>
        <div className="color-swatch" style={{ background: props.stroke || 'transparent' }}>
          <input type="color" value={toHex(props.stroke)} onChange={(e) => up({ stroke: e.target.value })} />
        </div>
        <input className="pb-input" type="number" placeholder="W" value={props.strokeWidth || 0}
          onChange={(e) => up({ strokeWidth: +e.target.value })} />
      </div>

      {/* Corner radius for rects */}
      {props.type === 'rect' && (
        <>
          <span className="pb-sep" />
          <div className="pb-group">
            <span className="pb-label">Radius</span>
            <input className="slider pb-slider" type="range" min="0" max="200" value={props.rx || 0}
              onChange={(e) => up({ rx: +e.target.value, ry: +e.target.value })} />
          </div>
        </>
      )}

      {/* Gradient fill */}
      {hasFill && (
        <>
          <span className="pb-sep" />
          <div className="pb-group">
            <span className="pb-label">Gradient</span>
            <Gradient engine={engine} />
          </div>
        </>
      )}

      {/* Shadow */}
      <span className="pb-sep" />
      <div className="pb-group">
        <span className="pb-label">Shadow</span>
        <Shadow engine={engine} hasShadow={!!props.shadow} />
      </div>

      {/* Image filters */}
      {props.type === 'image' && (
        <>
          <span className="pb-sep" />
          <div className="pb-group">
            <span className="pb-label">Filters</span>
            <Filters engine={engine} />
          </div>
        </>
      )}

      {/* Opacity */}
      <span className="pb-sep" />
      <div className="pb-group">
        <span className="pb-label">Opacity</span>
        <input className="slider pb-slider" type="range" min="0" max="1" step="0.01" value={props.opacity ?? 1}
          onChange={(e) => up({ opacity: +e.target.value })} />
      </div>
    </div>
  );
}

function Gradient({ engine }) {
  const [c1, setC1] = useState('#6c5ce7');
  const [c2, setC2] = useState('#00d2c3');
  const [type, setType] = useState('linear');
  const apply = () => engine.setGradient({ type, stops: [{ offset: 0, color: c1 }, { offset: 1, color: c2 }] });
  return (
    <>
      <div className="color-swatch" style={{ background: c1 }}><input type="color" value={c1} onChange={(e) => setC1(e.target.value)} /></div>
      <div className="color-swatch" style={{ background: c2 }}><input type="color" value={c2} onChange={(e) => setC2(e.target.value)} /></div>
      <select className="pb-input" value={type} onChange={(e) => setType(e.target.value)}>
        <option value="linear">Linear</option><option value="radial">Radial</option>
      </select>
      <button className="btn" onClick={apply}>Apply</button>
    </>
  );
}

function Shadow({ engine, hasShadow }) {
  const [on, setOn] = useState(hasShadow);
  const [blur, setBlur] = useState(10);
  const [color, setColor] = useState('#000000');
  useEffect(() => { setOn(hasShadow); }, [hasShadow]);
  const apply = (next) => { setOn(next); engine.setShadow({ enabled: next, color, blur, offsetX: 6, offsetY: 6 }); };
  return (
    <>
      <button className={`btn ${on ? 'primary' : ''}`} onClick={() => apply(!on)}>{on ? 'On' : 'Add'}</button>
      {on && (
        <>
          <div className="color-swatch" style={{ background: color }}>
            <input type="color" value={color} onChange={(e) => { setColor(e.target.value); engine.setShadow({ enabled: true, color: e.target.value, blur, offsetX: 6, offsetY: 6 }); }} />
          </div>
          <input className="slider pb-slider" type="range" min="0" max="50" value={blur}
            onChange={(e) => { setBlur(+e.target.value); engine.setShadow({ enabled: true, color, blur: +e.target.value, offsetX: 6, offsetY: 6 }); }} />
        </>
      )}
    </>
  );
}

function Filters({ engine }) {
  const [b, setB] = useState(0), [c, setC] = useState(0), [s, setS] = useState(0);
  return (
    <>
      <div className="btn-group">
        <button onClick={() => engine.applyImageFilter('grayscale', true)}>B&amp;W</button>
        <button onClick={() => engine.applyImageFilter('sepia', true)}>Sepia</button>
        <button onClick={() => engine.applyImageFilter('invert', true)}>Invert</button>
        <button onClick={() => { engine.resetImageFilters(); setB(0); setC(0); setS(0); }}>Reset</button>
      </div>
      <div className="pb-field" title="Brightness"><span>Br</span>
        <input className="slider pb-slider" type="range" min="-0.5" max="0.5" step="0.05" value={b}
          onChange={(e) => { setB(+e.target.value); engine.applyImageFilter('brightness', +e.target.value); }} /></div>
      <div className="pb-field" title="Contrast"><span>Co</span>
        <input className="slider pb-slider" type="range" min="-0.5" max="0.5" step="0.05" value={c}
          onChange={(e) => { setC(+e.target.value); engine.applyImageFilter('contrast', +e.target.value); }} /></div>
      <div className="pb-field" title="Saturation"><span>Sa</span>
        <input className="slider pb-slider" type="range" min="-1" max="1" step="0.1" value={s}
          onChange={(e) => { setS(+e.target.value); engine.applyImageFilter('saturation', +e.target.value); }} /></div>
    </>
  );
}

function toHex(c) {
  if (!c || typeof c !== 'string') return '#000000';
  if (c.startsWith('#')) return c.length === 4
    ? '#' + c.slice(1).split('').map((x) => x + x).join('') : c.slice(0, 7);
  return '#000000';
}
