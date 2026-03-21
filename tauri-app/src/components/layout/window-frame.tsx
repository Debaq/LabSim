import { useState, useRef, useCallback, useEffect } from "react";
import { X, Minus, Maximize2, Minimize2 } from "lucide-react";
import { useUIStore } from "@/stores/ui-store";

interface WindowFrameProps {
  id: string;
  title: string;
  children: React.ReactNode;
  initialX?: number;
  initialY?: number;
  initialWidth?: number;
  initialHeight?: number;
  onClose: () => void;
  onFocus: () => void;
  zIndex: number;
}

const MIN_W = 320;
const MIN_H = 200;
type ResizeDir = "n" | "s" | "e" | "w" | "ne" | "nw" | "se" | "sw" | null;

export function WindowFrame({
  id, title, children,
  initialX = 100, initialY = 50, initialWidth = 800, initialHeight = 550,
  onClose, onFocus, zIndex,
}: WindowFrameProps) {
  const [pos, setPos] = useState({ x: initialX, y: initialY });
  const [size, setSize] = useState({ w: initialWidth, h: initialHeight });
  const [maximized, setMaximized] = useState(false);
  const [preMaxState, setPreMaxState] = useState({ pos, size });
  const minimizeWindow = useUIStore((s) => s.minimizeWindow);
  const dragRef = useRef<{ startX: number; startY: number; origX: number; origY: number } | null>(null);
  const resizeRef = useRef<{ dir: ResizeDir; startX: number; startY: number; origX: number; origY: number; origW: number; origH: number } | null>(null);

  const onDragStart = useCallback((e: React.MouseEvent) => {
    if (maximized) return;
    e.preventDefault();
    onFocus();
    dragRef.current = { startX: e.clientX, startY: e.clientY, origX: pos.x, origY: pos.y };
  }, [maximized, pos, onFocus]);

  const onResizeStart = useCallback((dir: ResizeDir) => (e: React.MouseEvent) => {
    if (maximized) return;
    e.preventDefault(); e.stopPropagation(); onFocus();
    resizeRef.current = { dir, startX: e.clientX, startY: e.clientY, origX: pos.x, origY: pos.y, origW: size.w, origH: size.h };
  }, [maximized, pos, size, onFocus]);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (dragRef.current) {
        setPos({ x: dragRef.current.origX + (e.clientX - dragRef.current.startX), y: Math.max(0, dragRef.current.origY + (e.clientY - dragRef.current.startY)) });
      }
      if (resizeRef.current) {
        const r = resizeRef.current;
        const dx = e.clientX - r.startX, dy = e.clientY - r.startY;
        let nx = r.origX, ny = r.origY, nw = r.origW, nh = r.origH;
        if (r.dir?.includes("e")) nw = Math.max(MIN_W, r.origW + dx);
        if (r.dir?.includes("s")) nh = Math.max(MIN_H, r.origH + dy);
        if (r.dir?.includes("w")) { nw = Math.max(MIN_W, r.origW - dx); nx = r.origX + (r.origW - nw); }
        if (r.dir?.includes("n")) { nh = Math.max(MIN_H, r.origH - dy); ny = Math.max(0, r.origY + (r.origH - nh)); }
        setPos({ x: nx, y: ny }); setSize({ w: nw, h: nh });
      }
    };
    const onUp = () => { dragRef.current = null; resizeRef.current = null; };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => { window.removeEventListener("mousemove", onMove); window.removeEventListener("mouseup", onUp); };
  }, []);

  const toggleMaximize = () => {
    if (maximized) { setPos(preMaxState.pos); setSize(preMaxState.size); setMaximized(false); }
    else { setPreMaxState({ pos, size }); setPos({ x: 0, y: 0 }); setSize({ w: window.innerWidth, h: window.innerHeight - 44 }); setMaximized(true); }
  };

  const h = (dir: ResizeDir, cursor: string, style: React.CSSProperties) => (
    <div onMouseDown={onResizeStart(dir)} style={{ position: "absolute", zIndex: 10, cursor, ...style }} />
  );

  return (
    <div data-window-id={id}
      className="absolute flex flex-col overflow-visible rounded-lg shadow-2xl"
      style={{ left: pos.x, top: pos.y, width: size.w, height: size.h, zIndex, backgroundColor: "var(--ls-window-bg)", border: "1px solid var(--ls-border)" }}
      onMouseDown={onFocus}>

      {!maximized && (<>
        {h("n","ns-resize",{top:-3,left:10,right:10,height:6})}
        {h("s","ns-resize",{bottom:-3,left:10,right:10,height:6})}
        {h("w","ew-resize",{left:-3,top:10,bottom:10,width:6})}
        {h("e","ew-resize",{right:-3,top:10,bottom:10,width:6})}
        {h("nw","nwse-resize",{top:-4,left:-4,width:12,height:12})}
        {h("ne","nesw-resize",{top:-4,right:-4,width:12,height:12})}
        {h("sw","nesw-resize",{bottom:-4,left:-4,width:12,height:12})}
        {h("se","nwse-resize",{bottom:-4,right:-4,width:12,height:12})}
      </>)}

      <div className="flex h-9 shrink-0 cursor-move items-center justify-between border-b px-3 select-none"
        style={{ backgroundColor: "var(--ls-window-header)", borderColor: "var(--ls-border)" }}
        onMouseDown={onDragStart} onDoubleClick={toggleMaximize}>
        <span className="text-xs font-medium" style={{ color: "var(--ls-text)" }}>{title}</span>
        <div className="flex items-center gap-1">
          <button onClick={() => minimizeWindow(id)} className="flex h-5 w-5 items-center justify-center rounded ls-text-muted transition hover:ls-bg-input hover:ls-text"><Minus className="h-3 w-3" /></button>
          <button onClick={toggleMaximize} className="flex h-5 w-5 items-center justify-center rounded ls-text-muted transition hover:ls-bg-input hover:ls-text">{maximized ? <Minimize2 className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}</button>
          <button onClick={onClose} className="flex h-5 w-5 items-center justify-center rounded ls-text-muted transition hover:bg-red-500 hover:ls-text"><X className="h-3 w-3" /></button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
