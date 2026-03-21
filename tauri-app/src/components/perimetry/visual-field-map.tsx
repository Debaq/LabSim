import { useRef, useEffect } from "react";
import type { PointResult } from "@/lib/perimetry-config";
import { sensitivityToGray } from "@/lib/perimetry-config";
import { getThemeColors } from "@/lib/theme-canvas";

interface VisualFieldMapProps {
  points: PointResult[];
  currentPoint: number | null; // index of point being tested
  eye: "OD" | "OI";
  mode: "numeric" | "grayscale" | "deviation";
  onPointClick?: (index: number) => void;
}

export function VisualFieldMap({ points, currentPoint, eye, mode, onPointClick }: VisualFieldMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const size = Math.min(container.clientWidth, container.clientHeight);
    canvas.width = size;
    canvas.height = size;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const tc = getThemeColors();

    const cx = size / 2;
    const cy = size / 2;
    const scale = size / 70; // ±35 degrees maps to canvas

    // Background
    ctx.fillStyle = tc.canvasBg;
    ctx.fillRect(0, 0, size, size);

    // Concentric circles (eccentricity)
    ctx.strokeStyle = tc.gridLine;
    ctx.lineWidth = 1;
    for (const r of [10, 20, 30]) {
      ctx.beginPath();
      ctx.arc(cx, cy, r * scale, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Cross axes
    ctx.strokeStyle = tc.gridLineStrong;
    ctx.beginPath();
    ctx.moveTo(0, cy); ctx.lineTo(size, cy);
    ctx.moveTo(cx, 0); ctx.lineTo(cx, size);
    ctx.stroke();

    // Blind spot marker
    const bsX = eye === "OD" ? 15 : -15;
    ctx.fillStyle = tc.canvasSubtle;
    ctx.beginPath();
    ctx.arc(cx + bsX * scale, cy + 1.5 * scale, 3 * scale, 0, Math.PI * 2);
    ctx.fill();

    // Draw points
    points.forEach((pt, i) => {
      // Mirror x for left eye
      const px = cx + (eye === "OI" ? -pt.x : pt.x) * scale;
      const py = cy - pt.y * scale; // y is inverted (superior = up)

      const pointSize = scale * 2.5;
      const isCurrent = currentPoint === i;

      if (pt.sensitivity === null) {
        // Not tested yet
        ctx.fillStyle = isCurrent ? "rgba(255, 200, 0, 0.4)" : tc.gridLineStrong;
        ctx.beginPath();
        ctx.arc(px, py, pointSize / 2, 0, Math.PI * 2);
        ctx.fill();
      } else if (mode === "grayscale") {
        ctx.fillStyle = sensitivityToGray(pt.sensitivity);
        ctx.fillRect(px - pointSize, py - pointSize, pointSize * 2, pointSize * 2);
      } else if (mode === "numeric") {
        // Number
        ctx.fillStyle = pt.sensitivity < 10 ? "rgba(255,80,80,0.9)" : pt.sensitivity < 20 ? "rgba(255,200,50,0.9)" : "rgba(150,255,150,0.8)";
        ctx.font = `bold ${Math.max(8, scale * 1.8)}px monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(pt.sensitivity), px, py);
      } else if (mode === "deviation") {
        const dev = pt.totalDeviation ?? 0;
        if (tc.isLight) {
          // Light theme: darker = worse deficit
          if (dev < -10) ctx.fillStyle = "#e0e0e0";
          else if (dev < -5) ctx.fillStyle = "#b0b0b0";
          else if (dev < -2) ctx.fillStyle = "#707070";
          else ctx.fillStyle = "#333";
        } else {
          // Dark theme: original
          if (dev < -10) ctx.fillStyle = "#1a1a1a";
          else if (dev < -5) ctx.fillStyle = "#444";
          else if (dev < -2) ctx.fillStyle = "#888";
          else ctx.fillStyle = "#ccc";
        }
        ctx.fillRect(px - pointSize, py - pointSize, pointSize * 2, pointSize * 2);
      }

      // Current point highlight
      if (isCurrent) {
        ctx.strokeStyle = "rgba(255, 200, 0, 0.8)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(px, py, pointSize + 2, 0, Math.PI * 2);
        ctx.stroke();
      }
    });

    // Labels
    ctx.fillStyle = tc.canvasText;
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Superior", cx, 12);
    ctx.fillText("Inferior", cx, size - 4);
    ctx.textAlign = "left";
    ctx.fillText(eye === "OD" ? "Nasal" : "Temporal", 4, cy - 4);
    ctx.textAlign = "right";
    ctx.fillText(eye === "OD" ? "Temporal" : "Nasal", size - 4, cy - 4);

    // Eye label
    ctx.fillStyle = eye === "OD" ? "rgba(239,68,68,0.5)" : "rgba(96,165,250,0.5)";
    ctx.font = "bold 14px sans-serif";
    ctx.textAlign = "right";
    ctx.fillText(eye, size - 8, 16);

  }, [points, currentPoint, eye, mode]);

  // Resize
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => {
      // Trigger re-render
      const canvas = canvasRef.current;
      if (canvas) canvas.dispatchEvent(new Event("resize"));
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const handleClick = (e: React.MouseEvent) => {
    if (!onPointClick || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const size = canvasRef.current.width;
    const scale = size / 70;
    const cx = size / 2;
    const cy = size / 2;
    const mx = (e.clientX - rect.left) * (size / rect.width);
    const my = (e.clientY - rect.top) * (size / rect.height);

    // Find closest point
    let closest = -1;
    let minDist = Infinity;
    points.forEach((pt, i) => {
      const px = cx + pt.x * scale;
      const py = cy - pt.y * scale;
      const d = Math.sqrt((mx - px) ** 2 + (my - py) ** 2);
      if (d < minDist && d < scale * 4) {
        minDist = d;
        closest = i;
      }
    });
    if (closest >= 0) onPointClick(closest);
  };

  return (
    <div ref={containerRef} className="aspect-square w-full" onClick={handleClick}>
      <canvas ref={canvasRef} className="block h-full w-full rounded" style={{ imageRendering: "auto" }} />
    </div>
  );
}
