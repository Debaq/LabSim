import { useState, useRef, useCallback, useEffect } from "react";
import { X, Minus, Maximize2, Minimize2 } from "lucide-react";

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

export function WindowFrame({
  id,
  title,
  children,
  initialX = 100,
  initialY = 50,
  initialWidth = 800,
  initialHeight = 550,
  onClose,
  onFocus,
  zIndex,
}: WindowFrameProps) {
  const [pos, setPos] = useState({ x: initialX, y: initialY });
  const [size, setSize] = useState({ w: initialWidth, h: initialHeight });
  const [maximized, setMaximized] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [preMaxState, setPreMaxState] = useState({ pos, size });
  const dragRef = useRef<{ startX: number; startY: number; origX: number; origY: number } | null>(null);
  const frameRef = useRef<HTMLDivElement>(null);

  const onDragStart = useCallback(
    (e: React.MouseEvent) => {
      if (maximized) return;
      e.preventDefault();
      onFocus();
      dragRef.current = {
        startX: e.clientX,
        startY: e.clientY,
        origX: pos.x,
        origY: pos.y,
      };
    },
    [maximized, pos, onFocus],
  );

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!dragRef.current) return;
      const dx = e.clientX - dragRef.current.startX;
      const dy = e.clientY - dragRef.current.startY;
      setPos({
        x: dragRef.current.origX + dx,
        y: Math.max(0, dragRef.current.origY + dy),
      });
    };
    const onUp = () => {
      dragRef.current = null;
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  const toggleMaximize = () => {
    if (maximized) {
      setPos(preMaxState.pos);
      setSize(preMaxState.size);
      setMaximized(false);
    } else {
      setPreMaxState({ pos, size });
      setPos({ x: 0, y: 0 });
      setSize({ w: window.innerWidth, h: window.innerHeight - 40 });
      setMaximized(true);
    }
  };

  if (minimized) return null;

  return (
    <div
      ref={frameRef}
      data-window-id={id}
      className="absolute flex flex-col overflow-hidden rounded-lg shadow-2xl"
      style={{
        left: pos.x,
        top: pos.y,
        width: size.w,
        height: size.h,
        zIndex,
        backgroundColor: "var(--ls-window-bg)",
        border: "1px solid var(--ls-border)",
      }}
      onMouseDown={onFocus}
    >
      {/* Title bar */}
      <div
        className="flex h-9 shrink-0 cursor-move items-center justify-between border-b px-3 select-none"
        style={{ backgroundColor: "var(--ls-window-header)", borderColor: "var(--ls-border)" }}
        onMouseDown={onDragStart}
        onDoubleClick={toggleMaximize}
      >
        <span className="text-xs font-medium" style={{ color: "var(--ls-text)" }}>{title}</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setMinimized(true)}
            className="flex h-5 w-5 items-center justify-center rounded ls-text-muted transition hover:ls-bg-input hover:ls-text"
          >
            <Minus className="h-3 w-3" />
          </button>
          <button
            onClick={toggleMaximize}
            className="flex h-5 w-5 items-center justify-center rounded ls-text-muted transition hover:ls-bg-input hover:ls-text"
          >
            {maximized ? (
              <Minimize2 className="h-3 w-3" />
            ) : (
              <Maximize2 className="h-3 w-3" />
            )}
          </button>
          <button
            onClick={onClose}
            className="flex h-5 w-5 items-center justify-center rounded ls-text-muted transition hover:bg-red-500 hover:ls-text"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  );
}
