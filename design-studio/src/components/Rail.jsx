import { LayoutTemplate, Shapes, Type, Image, Upload, Layers, FolderHeart, Sticker } from 'lucide-react';
import { useEditor } from '../store/editorStore';

const ITEMS = [
  { id: 'templates', label: 'Templates', icon: LayoutTemplate },
  { id: 'elements', label: 'Elements', icon: Shapes },
  { id: 'text', label: 'Text', icon: Type },
  { id: 'stickers', label: 'Stickers', icon: Sticker },
  { id: 'images', label: 'Photos', icon: Image },
  { id: 'uploads', label: 'Uploads', icon: Upload },
  { id: 'mydesigns', label: 'Saved', icon: FolderHeart },
  { id: 'layers', label: 'Layers', icon: Layers },
];

export default function Rail() {
  const { activePanel, setActivePanel } = useEditor();
  return (
    <nav className="rail">
      {ITEMS.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          className={`rail-item ${activePanel === id ? 'active' : ''}`}
          onClick={() => setActivePanel(id)}
        >
          <Icon size={20} strokeWidth={1.8} />
          {label}
        </button>
      ))}
    </nav>
  );
}
