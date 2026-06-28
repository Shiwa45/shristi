import { fabric } from 'fabric';
import { toPx, GUIDE_COLORS, mmToPx } from '../config/printConfig';

// ============================================================
// CANVAS ENGINE
// Wraps a fabric.Canvas and adds everything a PRINT editor needs:
//  - document (trim) sizing in real units
//  - bleed / trim / safe guide overlays (non-selectable)
//  - per-side documents (front/back...)
//  - history (undo/redo)
//  - clipping to the bleed area for export
//  - serialization for saving to Django
// ============================================================

const GUIDE_META = '__guide';      // marks helper objects we exclude from export
const SIDE_KEY = '__side';

export class CanvasEngine {
  constructor(canvasEl, { onChange } = {}) {
    this.canvas = new fabric.Canvas(canvasEl, {
      backgroundColor: '#ffffff',
      preserveObjectStacking: true,
      controlsAboveOverlay: true,
      selection: true,
    });
    this.onChange = onChange || (() => {});
    this.product = null;
    this.docW = 0;
    this.docH = 0;
    this.bleedPx = 0;
    this.safePx = 0;
    this.activeSide = 'front';
    this.sideData = {};        // { front: fabricJSON, back: fabricJSON }
    this.guides = [];
    this.showFlags = { bleed: true, safe: true, trim: true, grid: false };

    this._history = [];
    this._historyIndex = -1;
    this._suspendHistory = false;

    this._bindEvents();
  }

  // ---------- Setup ----------
  _bindEvents() {
    const c = this.canvas;
    const emit = () => this.onChange();
    const recordable = () => { if (!this._suspendHistory) this._pushHistory(); this.onChange(); };

    c.on('object:added', emit);
    c.on('object:removed', emit);
    c.on('selection:created', emit);
    c.on('selection:updated', emit);
    c.on('selection:cleared', emit);
    c.on('object:modified', recordable);
    c.on('object:moving', (e) => this._handleSnap(e));
    c.on('text:changed', recordable);
  }

  applyProduct(product) {
    this.product = product;
    this.docW = toPx(product.width, product.unit);
    this.docH = toPx(product.height, product.unit);
    this.bleedPx = mmToPx(product.bleed || 0);
    this.safePx = mmToPx(product.safe || 0);
    // total canvas includes bleed on all sides
    const fullW = this.docW + this.bleedPx * 2;
    const fullH = this.docH + this.bleedPx * 2;
    this.canvas.setWidth(fullW);
    this.canvas.setHeight(fullH);
    this.fullW = fullW;
    this.fullH = fullH;
    this.drawGuides();
    this.fitToScreen();
    this._pushHistory();
  }

  // ---------- Guides (bleed / trim / safe) ----------
  drawGuides() {
    // remove old guides
    this.guides.forEach((g) => this.canvas.remove(g));
    this.guides = [];
    const c = this.canvas;
    const b = this.bleedPx;
    const s = this.safePx;

    const mk = (rect, color, dash) => {
      const r = new fabric.Rect({
        ...rect,
        fill: 'transparent',
        stroke: color,
        strokeWidth: 1.5,
        strokeDashArray: dash,
        selectable: false,
        evented: false,
        excludeFromExport: true,
        strokeUniform: true,
        [GUIDE_META]: true,
      });
      this.guides.push(r);
      c.add(r);
      r.bringToFront();
      return r;
    };

    // Bleed = full canvas edge
    if (this.showFlags.bleed && b > 0) {
      mk({ left: 0.75, top: 0.75, width: this.fullW - 1.5, height: this.fullH - 1.5 }, GUIDE_COLORS.bleed, [8, 6]);
    }
    // Trim = the actual document edge
    if (this.showFlags.trim) {
      mk({ left: b, top: b, width: this.docW, height: this.docH }, GUIDE_COLORS.trim, null);
    }
    // Safe = inset from trim
    if (this.showFlags.safe && s > 0) {
      mk({ left: b + s, top: b + s, width: this.docW - s * 2, height: this.docH - s * 2 }, GUIDE_COLORS.safe, [4, 4]);
    }
    if (this.showFlags.grid) this._drawGrid();
    c.requestRenderAll();
  }

  _drawGrid() {
    const step = mmToPx(10); // 1cm grid
    for (let x = this.bleedPx; x <= this.bleedPx + this.docW; x += step) {
      const line = new fabric.Line([x, this.bleedPx, x, this.bleedPx + this.docH], {
        stroke: 'rgba(0,0,0,0.08)', selectable: false, evented: false,
        excludeFromExport: true, [GUIDE_META]: true,
      });
      this.guides.push(line); this.canvas.add(line);
    }
    for (let y = this.bleedPx; y <= this.bleedPx + this.docH; y += step) {
      const line = new fabric.Line([this.bleedPx, y, this.bleedPx + this.docW, y], {
        stroke: 'rgba(0,0,0,0.08)', selectable: false, evented: false,
        excludeFromExport: true, [GUIDE_META]: true,
      });
      this.guides.push(line); this.canvas.add(line);
    }
  }

  setGuideFlags(flags) {
    this.showFlags = { ...this.showFlags, ...flags };
    this.drawGuides();
  }

  // ---------- Snapping ----------
  _handleSnap(e) {
    if (!this._snap) return;
    const obj = e.target;
    const threshold = 6;
    const cx = this.fullW / 2;
    const cy = this.fullH / 2;
    const center = obj.getCenterPoint();
    if (Math.abs(center.x - cx) < threshold) obj.setPositionByOrigin(new fabric.Point(cx, center.y), 'center', 'center');
    if (Math.abs(center.y - cy) < threshold) obj.setPositionByOrigin(new fabric.Point(obj.getCenterPoint().x, cy), 'center', 'center');
  }
  setSnap(on) { this._snap = on; }

  // ---------- Zoom / view ----------
  setZoom(zoom) {
    this.canvas.setZoom(zoom);
    this.canvas.setWidth(this.fullW * zoom);
    this.canvas.setHeight(this.fullH * zoom);
    this.canvas.requestRenderAll();
  }

  fitToScreen(padding = 80) {
    const wrap = this.canvas.wrapperEl?.parentElement;
    if (!wrap) return 1;
    const availW = wrap.clientWidth - padding;
    const availH = wrap.clientHeight - padding;
    const zoom = Math.min(availW / this.fullW, availH / this.fullH, 2);
    this.setZoom(zoom > 0 ? zoom : 1);
    return zoom;
  }

  // ---------- Object factory ----------
  _add(obj, { center = true } = {}) {
    if (center) {
      obj.set({
        left: this.fullW / 2,
        top: this.fullH / 2,
        originX: 'center',
        originY: 'center',
      });
    }
    this.canvas.add(obj);
    this.canvas.setActiveObject(obj);
    obj.bringToFront();
    this.guides.forEach((g) => g.bringToFront());
    this.canvas.requestRenderAll();
    this._pushHistory();
    return obj;
  }

  addText(text = 'Your text', opts = {}) {
    const t = new fabric.Textbox(text, {
      fontFamily: 'Poppins', fontSize: 80, fill: '#1a1a1a',
      width: this.docW * 0.6, textAlign: 'left', ...opts,
    });
    return this._add(t);
  }

  addRect() {
    return this._add(new fabric.Rect({ width: this.docW * 0.4, height: this.docW * 0.4, fill: '#2f6fed', rx: 0, ry: 0 }));
  }
  addCircle() {
    return this._add(new fabric.Circle({ radius: this.docW * 0.2, fill: '#e0457b' }));
  }
  addTriangle() {
    return this._add(new fabric.Triangle({ width: this.docW * 0.4, height: this.docW * 0.4, fill: '#2fa84f' }));
  }
  addLine() {
    return this._add(new fabric.Line([0, 0, this.docW * 0.5, 0], { stroke: '#1a1a1a', strokeWidth: 8 }));
  }
  addEllipse() {
    return this._add(new fabric.Ellipse({ rx: this.docW * 0.25, ry: this.docW * 0.15, fill: '#8e44ad' }));
  }

  // Regular polygon (pentagon/hexagon/etc) by side count.
  addPolygon(sides = 5) {
    const r = this.docW * 0.2;
    const pts = [];
    for (let i = 0; i < sides; i++) {
      const a = (Math.PI * 2 * i) / sides - Math.PI / 2;
      pts.push({ x: r + r * Math.cos(a), y: r + r * Math.sin(a) });
    }
    return this._add(new fabric.Polygon(pts, { fill: '#16a085' }));
  }

  // Star with configurable points + inner radius ratio.
  addStar(points = 5, innerRatio = 0.5) {
    const outer = this.docW * 0.2, inner = outer * innerRatio;
    const pts = [];
    for (let i = 0; i < points * 2; i++) {
      const r = i % 2 === 0 ? outer : inner;
      const a = (Math.PI * i) / points - Math.PI / 2;
      pts.push({ x: outer + r * Math.cos(a), y: outer + r * Math.sin(a) });
    }
    return this._add(new fabric.Polygon(pts, { fill: '#f5a623' }));
  }

  // Heart via SVG path.
  addHeart() {
    const path = 'M 50 30 C 50 30 35 0 17 12 C 0 24 5 50 50 80 C 95 50 100 24 83 12 C 65 0 50 30 50 30 z';
    const p = new fabric.Path(path, { fill: '#e0457b' });
    p.scaleToWidth(this.docW * 0.35);
    return this._add(p);
  }

  // Arrow.
  addArrow() {
    const path = 'M 0 20 L 50 20 L 50 5 L 80 30 L 50 55 L 50 40 L 0 40 z';
    const p = new fabric.Path(path, { fill: '#2f6fed' });
    p.scaleToWidth(this.docW * 0.4);
    return this._add(p);
  }

  // Speech bubble.
  addSpeechBubble() {
    const path = 'M 10 10 H 90 a10 10 0 0 1 10 10 V 60 a10 10 0 0 1 -10 10 H 40 L 20 90 V 70 H 10 a10 10 0 0 1 -10 -10 V 20 a10 10 0 0 1 10 -10 z';
    const p = new fabric.Path(path, { fill: '#34495e' });
    p.scaleToWidth(this.docW * 0.4);
    return this._add(p);
  }

  addImageFromUrl(url, opts = {}) {
    return new Promise((resolve) => {
      fabric.Image.fromURL(url, (img) => {
        const scale = Math.min((this.docW * 0.6) / img.width, (this.docH * 0.6) / img.height, 1);
        img.scale(scale);
        this._add(img);
        resolve(img);
      }, { crossOrigin: 'anonymous', ...opts });
    });
  }

  addStickerFromUrl(url) {
    if (url.toLowerCase().endsWith('.svg')) {
      return fetch(url)
        .then((r) => r.text())
        .then((svg) => new Promise((resolve) => {
          fabric.loadSVGFromString(svg, (objects, options) => {
            const group = fabric.util.groupSVGElements(objects, options);
            const scale = Math.min(
              (this.docW * 0.4) / (group.width || 100),
              (this.docH * 0.4) / (group.height || 100),
              1,
            );
            group.scale(scale);
            this._add(group);
            resolve(group);
          });
        }));
    }
    return new Promise((resolve) => {
      fabric.Image.fromURL(url, (img) => {
        const scale = Math.min(
          (this.docW * 0.4) / img.width,
          (this.docH * 0.4) / img.height,
          1,
        );
        img.scale(scale);
        this._add(img);
        resolve(img);
      }, { crossOrigin: 'anonymous' });
    });
  }

  addSvgString(svg, opts = {}) {
    return new Promise((resolve) => {
      fabric.loadSVGFromString(svg, (objects, options) => {
        const group = fabric.util.groupSVGElements(objects, options);
        const scale = Math.min((this.docW * 0.4) / (group.width || 100), 1);
        group.scale(scale);
        this._add(group);
        resolve(group);
      });
    });
  }

  // ---------- Templates (SVG) ----------
  loadSvgTemplate(svg) {
    return new Promise((resolve) => {
      fabric.loadSVGFromString(svg, (objects, options) => {
        this._suspendHistory = true;
        this._clearContent();

        // Group all elements so we can measure & scale the whole template
        const group = fabric.util.groupSVGElements(objects, options);
        const svgW = group.width  || 1;
        const svgH = group.height || 1;

        // Contain-fit: scale uniformly so the template fills the trim area
        // without any distortion (same logic as CSS object-fit: contain)
        const scale = Math.min(this.docW / svgW, this.docH / svgH);
        const scaledW = svgW * scale;
        const scaledH = svgH * scale;

        group.set({
          left:    this.bleedPx + (this.docW - scaledW) / 2,
          top:     this.bleedPx + (this.docH - scaledH) / 2,
          originX: 'left',
          originY: 'top',
          scaleX:  scale,
          scaleY:  scale,
        });
        group.setCoords();

        // Add the group, then ungroup so every element is individually editable
        this.canvas.add(group);
        this.canvas.setActiveObject(group);
        this.canvas.getActiveObject().toActiveSelection();
        this.canvas.discardActiveObject();

        // Flatten any nested SVG <g> groups (SVG files can have many nesting levels)
        this._flattenGroups();
        // Convert fabric.Text → fabric.IText so double-click editing works on text
        this._upgradeTextObjects();

        this.guides.forEach((g) => g.bringToFront());
        this._suspendHistory = false;
        this.canvas.requestRenderAll();
        this._pushHistory();
        this.onChange();
        resolve();
      });
    });
  }

  // Recursively ungroup any fabric.Group that came from SVG <g> elements
  _flattenGroups() {
    let found = true;
    while (found) {
      found = false;
      const groups = this.canvas.getObjects().filter(
        (o) => !o[GUIDE_META] && o.type === 'group'
      );
      if (!groups.length) break;
      found = true;
      groups.forEach((g) => {
        this.canvas.setActiveObject(g);
        const active = this.canvas.getActiveObject();
        if (active && active.toActiveSelection) {
          active.toActiveSelection();
          this.canvas.discardActiveObject();
        }
      });
    }
  }

  // SVG loading creates non-editable fabric.Text; replace with fabric.IText
  // so double-click enters text-edit mode and the right panel shows text controls.
  _upgradeTextObjects() {
    const texts = this.canvas.getObjects().filter(
      (o) => !o[GUIDE_META] && o.type === 'text'
    );
    texts.forEach((old) => {
      const itext = new fabric.IText(old.text || '', {
        left:        old.left,
        top:         old.top,
        width:       old.width,
        scaleX:      old.scaleX,
        scaleY:      old.scaleY,
        angle:       old.angle,
        originX:     old.originX,
        originY:     old.originY,
        skewX:       old.skewX,
        skewY:       old.skewY,
        opacity:     old.opacity,
        fill:        old.fill,
        stroke:      old.stroke,
        strokeWidth: old.strokeWidth,
        fontFamily:  old.fontFamily,
        fontSize:    old.fontSize,
        fontWeight:  old.fontWeight,
        fontStyle:   old.fontStyle,
        textAlign:   old.textAlign,
        lineHeight:  old.lineHeight,
        charSpacing: old.charSpacing,
        underline:   old.underline,
        overline:    old.overline,
        linethrough: old.linethrough,
        styles:      old.styles || {},
      });
      const idx = this.canvas.getObjects().indexOf(old);
      this.canvas.remove(old);
      this.canvas.insertAt(itext, idx);
    });
  }

  loadFabricJSON(json) {
    return new Promise((resolve) => {
      this._suspendHistory = true;
      this.canvas.loadFromJSON(json, () => {
        // re-add guides on top
        this.drawGuides();
        this._suspendHistory = false;
        this.canvas.requestRenderAll();
        this._pushHistory();
        this.onChange();
        resolve();
      });
    });
  }

  _clearContent() {
    this.canvas.getObjects().forEach((o) => {
      if (!o[GUIDE_META]) this.canvas.remove(o);
    });
  }

  // ---------- Selection / object ops ----------
  getActive() { return this.canvas.getActiveObject(); }

  updateActive(props) {
    const o = this.getActive();
    if (!o) return;
    o.set(props);
    o.setCoords();
    this.canvas.requestRenderAll();
    this._pushHistory();
    this.onChange();
  }

  deleteSelected() {
    const objs = this.canvas.getActiveObjects();
    objs.forEach((o) => { if (!o[GUIDE_META]) this.canvas.remove(o); });
    this.canvas.discardActiveObject();
    this.canvas.requestRenderAll();
    this._pushHistory();
  }

  duplicateSelected() {
    const o = this.getActive();
    if (!o) return;
    o.clone((clone) => {
      clone.set({ left: o.left + 20, top: o.top + 20 });
      this.canvas.add(clone);
      this.canvas.setActiveObject(clone);
      this.guides.forEach((g) => g.bringToFront());
      this.canvas.requestRenderAll();
      this._pushHistory();
    });
  }

  bringForward() { const o = this.getActive(); if (o) { o.bringForward(); this.guides.forEach(g=>g.bringToFront()); this._after(); } }
  sendBackward() { const o = this.getActive(); if (o) { o.sendBackwards(); this._after(); } }
  bringToFront() { const o = this.getActive(); if (o) { o.bringToFront(); this.guides.forEach(g=>g.bringToFront()); this._after(); } }
  sendToBack() { const o = this.getActive(); if (o) { o.sendToBack(); this._after(); } }

  align(type) {
    const o = this.getActive();
    if (!o) return;
    const L = this.bleedPx, T = this.bleedPx, R = this.bleedPx + this.docW, B = this.bleedPx + this.docH;
    const w = o.getScaledWidth(), h = o.getScaledHeight();
    o.set({ originX: 'left', originY: 'top' });
    switch (type) {
      case 'left': o.set({ left: L }); break;
      case 'centerH': o.set({ left: (L + R) / 2 - w / 2 }); break;
      case 'right': o.set({ left: R - w }); break;
      case 'top': o.set({ top: T }); break;
      case 'centerV': o.set({ top: (T + B) / 2 - h / 2 }); break;
      case 'bottom': o.set({ top: B - h }); break;
    }
    o.setCoords();
    this._after();
  }

  flip(axis) {
    const o = this.getActive();
    if (!o) return;
    o.set(axis === 'x' ? { flipX: !o.flipX } : { flipY: !o.flipY });
    this._after();
  }

  group() {
    const sel = this.canvas.getActiveObject();
    if (!sel || sel.type !== 'activeSelection') return;
    sel.toGroup();
    this._after();
  }
  ungroup() {
    const sel = this.canvas.getActiveObject();
    if (!sel || sel.type !== 'group') return;
    sel.toActiveSelection();
    this._after();
  }

  toggleLock() {
    const o = this.getActive();
    if (!o) return;
    const locked = !o.lockMovementX;
    o.set({
      lockMovementX: locked, lockMovementY: locked,
      lockScalingX: locked, lockScalingY: locked,
      lockRotation: locked, hasControls: !locked, editable: !locked,
    });
    this._after();
  }

  setVisible(obj, visible) { obj.set({ visible }); this._after(); }

  _after() {
    this.canvas.requestRenderAll();
    this._pushHistory();
    this.onChange();
  }

  // ---------- Layers list ----------
  getLayers() {
    return this.canvas.getObjects()
      .filter((o) => !o[GUIDE_META])
      .map((o, i) => ({
        id: o.__id || (o.__id = 'obj_' + Math.random().toString(36).slice(2, 9)),
        name: o.__name || this._defaultName(o),
        type: o.type,
        visible: o.visible !== false,
        locked: !!o.lockMovementX,
        ref: o,
        selected: this.canvas.getActiveObjects().includes(o),
      }))
      .reverse(); // top layer first
  }

  _defaultName(o) {
    if (o.type === 'textbox' || o.type === 'i-text' || o.type === 'text') return o.text?.slice(0, 18) || 'Text';
    if (o.type === 'image') return 'Image';
    if (o.type === 'group') return 'Group';
    return o.type.charAt(0).toUpperCase() + o.type.slice(1);
  }

  selectById(id) {
    const o = this.canvas.getObjects().find((x) => x.__id === id);
    if (o) { this.canvas.setActiveObject(o); this.canvas.requestRenderAll(); this.onChange(); }
  }
  renameLayer(id, name) {
    const o = this.canvas.getObjects().find((x) => x.__id === id);
    if (o) { o.__name = name; this.onChange(); }
  }
  reorderLayer(id, direction) {
    const o = this.canvas.getObjects().find((x) => x.__id === id);
    if (!o) return;
    direction === 'up' ? o.bringForward() : o.sendBackwards();
    this.guides.forEach((g) => g.bringToFront());
    this._after();
  }

  // ---------- History ----------
  _pushHistory() {
    if (this._suspendHistory) return;
    const json = JSON.stringify(this._exportableJSON());
    // trim redo branch
    this._history = this._history.slice(0, this._historyIndex + 1);
    this._history.push(json);
    if (this._history.length > 60) this._history.shift();
    this._historyIndex = this._history.length - 1;
    this.onChange();
  }

  _exportableJSON() {
    return this.canvas.toJSON(['__id', '__name', 'selectable', 'lockMovementX', 'lockMovementY', 'lockScalingX', 'lockScalingY', 'lockRotation']);
  }

  undo() {
    if (this._historyIndex <= 0) return;
    this._historyIndex--;
    this._restore(this._history[this._historyIndex]);
  }
  redo() {
    if (this._historyIndex >= this._history.length - 1) return;
    this._historyIndex++;
    this._restore(this._history[this._historyIndex]);
  }
  _restore(json) {
    this._suspendHistory = true;
    this.canvas.loadFromJSON(json, () => {
      this.drawGuides();
      this._suspendHistory = false;
      this.canvas.requestRenderAll();
      this.onChange();
    });
  }
  canUndo() { return this._historyIndex > 0; }
  canRedo() { return this._historyIndex < this._history.length - 1; }

  // ---------- Multi-side ----------
  switchSide(side) {
    // save current
    this.sideData[this.activeSide] = this._exportableJSON();
    this.activeSide = side;
    const data = this.sideData[side];
    if (data) {
      this.loadFabricJSON(data);
    } else {
      this._clearContent();
      this.canvas.requestRenderAll();
    }
  }

  // ---------- Curved / arc text ----------
  // Re-renders a textbox onto a curved baseline. Stores curve amount
  // on the object so the slider can keep adjusting it.
  setTextCurve(amount) {
    const o = this.getActive();
    if (!o || !o.type?.includes('text')) return;
    o.__curve = amount;
    // We approximate curved text by converting to a path-following group.
    // Simpler robust approach: store curve and apply skew/arc via path.
    // Use fabric's built-in 'path' on Text if available; otherwise fake with transform.
    if (amount === 0) {
      o.set({ path: null });
    } else {
      const text = o.text || '';
      const w = o.width || 200;
      const r = (w * 100) / (Math.abs(amount) || 1); // radius from curve %
      const sweep = amount > 0 ? 1 : 0;
      const dir = amount > 0 ? 1 : -1;
      const pathStr = `M 0 0 A ${r} ${r} 0 0 ${sweep} ${w} ${dir * 0.001}`;
      const path = new fabric.Path(pathStr, { visible: false });
      o.set({ path });
    }
    o.setCoords();
    this._after();
  }

  // ---------- Image filters ----------
  applyImageFilter(filterName, value) {
    const o = this.getActive();
    if (!o || o.type !== 'image') return;
    const F = fabric.Image.filters;
    o.filters = (o.filters || []).filter((f) => f.__name !== filterName);
    let filter = null;
    switch (filterName) {
      case 'grayscale': if (value) filter = new F.Grayscale(); break;
      case 'sepia': if (value) filter = new F.Sepia(); break;
      case 'invert': if (value) filter = new F.Invert(); break;
      case 'brightness': filter = new F.Brightness({ brightness: value }); break;
      case 'contrast': filter = new F.Contrast({ contrast: value }); break;
      case 'saturation': filter = new F.Saturation({ saturation: value }); break;
      case 'blur': filter = new F.Blur({ blur: value }); break;
      default: break;
    }
    if (filter) { filter.__name = filterName; o.filters.push(filter); }
    o.applyFilters();
    this._after();
  }
  resetImageFilters() {
    const o = this.getActive();
    if (!o || o.type !== 'image') return;
    o.filters = []; o.applyFilters(); this._after();
  }

  // Crop/replace helpers
  replaceImage(url) {
    const o = this.getActive();
    if (!o || o.type !== 'image') return;
    o.setSrc(url, () => { this.canvas.requestRenderAll(); this._after(); }, { crossOrigin: 'anonymous' });
  }

  // ---------- Shadow ----------
  setShadow({ enabled, color = 'rgba(0,0,0,0.3)', blur = 10, offsetX = 5, offsetY = 5 }) {
    const o = this.getActive();
    if (!o) return;
    o.set('shadow', enabled ? new fabric.Shadow({ color, blur, offsetX, offsetY }) : null);
    this._after();
  }

  // ---------- Gradient fill ----------
  setGradient({ type = 'linear', stops }) {
    const o = this.getActive();
    if (!o) return;
    const w = o.width || 100, h = o.height || 100;
    const coords = type === 'linear'
      ? { x1: 0, y1: 0, x2: w, y2: h }
      : { x1: w / 2, y1: h / 2, r1: 0, x2: w / 2, y2: h / 2, r2: Math.max(w, h) / 2 };
    o.set('fill', new fabric.Gradient({ type, coords, colorStops: stops }));
    this._after();
  }
  setSolidFill(color) {
    const o = this.getActive();
    if (!o) return;
    o.set('fill', color);
    this._after();
  }

  // ---------- Free draw ----------
  setDrawing(on, { color = '#1a1a1a', width = 6 } = {}) {
    this.canvas.isDrawingMode = on;
    if (on) {
      this.canvas.freeDrawingBrush = new fabric.PencilBrush(this.canvas);
      this.canvas.freeDrawingBrush.color = color;
      this.canvas.freeDrawingBrush.width = width;
    }
  }
  setBrush({ color, width }) {
    if (!this.canvas.freeDrawingBrush) return;
    if (color != null) this.canvas.freeDrawingBrush.color = color;
    if (width != null) this.canvas.freeDrawingBrush.width = width;
  }

  // ---------- QR code (expects a dataURL from qrcode lib) ----------
  addQRCode(dataUrl) {
    return this.addImageFromUrl(dataUrl);
  }

  // ---------- Background ----------
  setBackgroundColor(color) {
    this.canvas.setBackgroundColor(color, () => this.canvas.requestRenderAll());
    this._bg = color;
    this._pushHistory();
    this.onChange();
  }

  // ---------- Distribute / align multiple ----------
  distribute(axis) {
    const sel = this.canvas.getActiveObject();
    if (!sel || sel.type !== 'activeSelection') return;
    const objs = sel.getObjects().slice().sort((a, b) =>
      axis === 'h' ? a.left - b.left : a.top - b.top);
    if (objs.length < 3) return;
    const first = objs[0], last = objs[objs.length - 1];
    const start = axis === 'h' ? first.left : first.top;
    const end = axis === 'h' ? last.left : last.top;
    const gap = (end - start) / (objs.length - 1);
    objs.forEach((o, i) => { axis === 'h' ? (o.left = start + gap * i) : (o.top = start + gap * i); });
    this._after();
  }

  // ---------- Opacity helper for selection ----------
  setSelectionProp(prop, value) {
    this.canvas.getActiveObjects().forEach((o) => o.set(prop, value));
    this._after();
  }

  // ---------- Preflight check (print readiness) ----------
  // Flags objects outside the safe area or low-res raster images.
  preflight() {
    const issues = [];
    const safeL = this.bleedPx + this.safePx;
    const safeT = this.bleedPx + this.safePx;
    const safeR = this.bleedPx + this.docW - this.safePx;
    const safeB = this.bleedPx + this.docH - this.safePx;
    this.canvas.getObjects().forEach((o) => {
      if (o[GUIDE_META]) return;
      const b = o.getBoundingRect(true);
      if (b.left < safeL || b.top < safeT || b.left + b.width > safeR || b.top + b.height > safeB) {
        issues.push({ type: 'outside-safe', name: o.__name || o.type });
      }
      if (o.type === 'image' && o._element) {
        const natW = o._element.naturalWidth || o.width;
        const renderedW = o.getScaledWidth();
        const effectiveDpi = (natW / renderedW) * 300;
        if (effectiveDpi < 150) issues.push({ type: 'low-res', name: o.__name || 'Image', dpi: Math.round(effectiveDpi) });
      }
    });
    return issues;
  }


  // Returns a high-res PNG of the TRIM area (what gets printed),
  // optionally including bleed for the print shop.
  exportPNG({ includeBleed = true, multiplier = 1 } = {}) {
    this.canvas.discardActiveObject();
    const wasVisible = this.guides.map((g) => g.visible);
    this.guides.forEach((g) => (g.visible = false));
    this.canvas.requestRenderAll();

    const opts = includeBleed
      ? { left: 0, top: 0, width: this.fullW, height: this.fullH }
      : { left: this.bleedPx, top: this.bleedPx, width: this.docW, height: this.docH };

    const dataUrl = this.canvas.toDataURL({
      format: 'png', multiplier, ...opts,
    });

    this.guides.forEach((g, i) => (g.visible = wasVisible[i]));
    this.canvas.requestRenderAll();
    return dataUrl;
  }

  exportSVG() {
    this.guides.forEach((g) => (g.visible = false));
    const svg = this.canvas.toSVG();
    this.guides.forEach((g) => (g.visible = true));
    this.canvas.requestRenderAll();
    return svg;
  }

  serialize() {
    this.sideData[this.activeSide] = this._exportableJSON();
    return {
      product: this.product,
      sides: this.sideData,
      activeSide: this.activeSide,
      background: this._bg || '#ffffff',
    };
  }

  dispose() { this.canvas.dispose(); }
}
