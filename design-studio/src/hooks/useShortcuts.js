import { useEffect } from 'react';
import { useEditor } from '../store/editorStore';

// ============================================================
// KEYBOARD SHORTCUTS
// Full desktop/laptop coverage. Ignores typing into inputs and
// while editing text on the canvas.
// ============================================================

export function useShortcuts() {
  const engine = useEditor((s) => s.engine);

  useEffect(() => {
    if (!engine) return;

    const isTyping = (e) => {
      const t = e.target;
      const tag = t.tagName;
      return tag === 'INPUT' || tag === 'TEXTAREA' || t.isContentEditable;
    };
    const editingCanvasText = () => {
      const o = engine.getActive();
      return o && (o.isEditing === true);
    };

    const nudge = (dx, dy) => {
      const o = engine.getActive();
      if (!o) return;
      o.set({ left: o.left + dx, top: o.top + dy });
      o.setCoords();
      engine.canvas.requestRenderAll();
    };

    const handler = (e) => {
      if (isTyping(e) || editingCanvasText()) {
        // allow ctrl+z etc inside text? let browser handle text editing
        return;
      }
      const mod = e.ctrlKey || e.metaKey;
      const key = e.key.toLowerCase();

      // ----- with modifier -----
      if (mod) {
        switch (key) {
          case 'z': e.preventDefault(); e.shiftKey ? engine.redo() : engine.undo(); return;
          case 'y': e.preventDefault(); engine.redo(); return;
          case 'd': e.preventDefault(); engine.duplicateSelected(); return;
          case 'c': e.preventDefault(); engine._clipboard = engine.getActive(); return;
          case 'v': e.preventDefault();
            if (engine._clipboard) {
              engine._clipboard.clone((c) => {
                c.set({ left: c.left + 24, top: c.top + 24 });
                engine.canvas.add(c); engine.canvas.setActiveObject(c);
                engine.guides.forEach((g) => g.bringToFront());
                engine._after();
              });
            }
            return;
          case 'a': e.preventDefault();
            engine.canvas.discardActiveObject();
            const sel = new (engine.canvas.__proto__.constructor ? window.fabric?.ActiveSelection : Object)();
            return;
          case 'g': e.preventDefault(); e.shiftKey ? engine.ungroup() : engine.group(); return;
          case ']': e.preventDefault(); engine.bringForward(); return;
          case '[': e.preventDefault(); engine.sendBackward(); return;
          case 's': e.preventDefault(); window.dispatchEvent(new CustomEvent('ds:save')); return;
          case '=': case '+': e.preventDefault(); {
            const z = Math.min(engine.canvas.getZoom() * 1.1, 4); engine.setZoom(z);
            useEditor.getState().update({ zoom: z }); return;
          }
          case '-': e.preventDefault(); {
            const z = Math.max(engine.canvas.getZoom() / 1.1, 0.05); engine.setZoom(z);
            useEditor.getState().update({ zoom: z }); return;
          }
          case '0': e.preventDefault(); { const z = engine.fitToScreen(); useEditor.getState().update({ zoom: z }); return; }
          default: break;
        }
      }

      // ----- no modifier -----
      switch (e.key) {
        case 'Delete': case 'Backspace': e.preventDefault(); engine.deleteSelected(); break;
        case 'Escape': engine.canvas.discardActiveObject(); engine.canvas.requestRenderAll(); break;
        case 'ArrowLeft': e.preventDefault(); nudge(e.shiftKey ? -10 : -1, 0); break;
        case 'ArrowRight': e.preventDefault(); nudge(e.shiftKey ? 10 : 1, 0); break;
        case 'ArrowUp': e.preventDefault(); nudge(0, e.shiftKey ? -10 : -1); break;
        case 'ArrowDown': e.preventDefault(); nudge(0, e.shiftKey ? 10 : 1); break;
        case 'l': case 'L': engine.toggleLock(); break;
        default: break;
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [engine]);
}
