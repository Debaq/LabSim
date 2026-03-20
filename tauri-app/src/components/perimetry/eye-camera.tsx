import { useRef, useEffect } from "react";
import { getThemeColors } from "@/lib/theme-canvas";

interface EyeCameraProps {
  isFixating: boolean;
  isRunning: boolean;
  eye: "OD" | "OI";
}

export function EyeCamera({ isFixating, isRunning, eye }: EyeCameraProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const tc = getThemeColors();

    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;

    // Dark IR-like background
    ctx.fillStyle = tc.canvasBg;
    ctx.fillRect(0, 0, w, h);

    // Slight IR noise texture
    for (let i = 0; i < 200; i++) {
      ctx.fillStyle = `rgba(40,20,15,${Math.random() * 0.3})`;
      ctx.fillRect(Math.random() * w, Math.random() * h, 2, 2);
    }

    // Iris (dark circle)
    const irisR = Math.min(w, h) * 0.38;
    const grad = ctx.createRadialGradient(cx, cy, irisR * 0.3, cx, cy, irisR);
    grad.addColorStop(0, "#1a1410");
    grad.addColorStop(0.6, "#2a1f18");
    grad.addColorStop(1, "#3a2820");
    ctx.beginPath();
    ctx.arc(cx, cy, irisR, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // Pupil
    const pupilR = irisR * 0.45;
    // Pupil position shifts slightly when not fixating
    const px = cx + (isFixating ? 0 : (Math.random() - 0.5) * 8);
    const py = cy + (isFixating ? 0 : (Math.random() - 0.5) * 6);
    ctx.beginPath();
    ctx.arc(px, py, pupilR, 0, Math.PI * 2);
    ctx.fillStyle = "#050303";
    ctx.fill();

    // Pupil highlight (IR reflection = fixation target)
    ctx.beginPath();
    ctx.arc(px - pupilR * 0.2, py - pupilR * 0.25, pupilR * 0.15, 0, Math.PI * 2);
    ctx.fillStyle = isFixating ? "rgba(255,255,200,0.7)" : "rgba(255,100,100,0.5)";
    ctx.fill();

    // Fixation crosshair overlay
    if (isRunning) {
      ctx.strokeStyle = isFixating ? "rgba(0,255,100,0.3)" : "rgba(255,50,50,0.4)";
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(cx - 15, cy); ctx.lineTo(cx + 15, cy);
      ctx.moveTo(cx, cy - 15); ctx.lineTo(cx, cy + 15);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Eye label
    ctx.fillStyle = tc.canvasText;
    ctx.font = "8px monospace";
    ctx.fillText(eye, 4, 10);

    // IR indicator
    ctx.fillStyle = "rgba(255,50,50,0.4)";
    ctx.beginPath();
    ctx.arc(w - 8, 8, 3, 0, Math.PI * 2);
    ctx.fill();

  }, [isFixating, isRunning, eye]);

  return (
    <div className="rounded border ls-border bg-black overflow-hidden">
      <div className="px-1.5 py-0.5 text-[7px] font-bold uppercase tracking-wider ls-text-muted ls-bg-panel2">
        Cámara IR
      </div>
      <canvas ref={canvasRef} width={160} height={120} className="block w-full" />
    </div>
  );
}
