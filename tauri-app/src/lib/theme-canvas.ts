// Read CSS custom properties for use in canvas drawing
export function getThemeColors() {
  const root = document.documentElement;
  const get = (v: string) => getComputedStyle(root).getPropertyValue(v).trim();

  const panel = get("--ls-panel") || "#1a2332";
  const panel2 = get("--ls-panel-secondary") || "#0f1923";
  const text = get("--ls-text") || "#e2e8f0";
  const text2 = get("--ls-text-secondary") || "#94a3b8";
  const muted = get("--ls-text-muted") || "#475569";
  const border = get("--ls-border") || "rgba(255,255,255,0.08)";
  const accent = get("--ls-accent") || "#3b82f6";
  const bg = get("--ls-window-bg") || "#1e293b";

  // Detect if light theme by checking text luminance
  const isLight = isLightColor(text);

  return {
    bg, panel, panel2, text, text2, muted, border, accent,
    // Canvas-specific helpers
    gridLine: isLight ? "rgba(0,0,0,0.08)" : "rgba(255,255,255,0.06)",
    gridLineStrong: isLight ? "rgba(0,0,0,0.15)" : "rgba(255,255,255,0.1)",
    canvasBg: isLight ? "#f0f3f7" : "#0a0a0a",
    canvasText: isLight ? "rgba(0,0,0,0.5)" : "rgba(255,255,255,0.4)",
    canvasTextStrong: isLight ? "rgba(0,0,0,0.7)" : "rgba(255,255,255,0.6)",
    canvasSubtle: isLight ? "rgba(0,0,0,0.04)" : "rgba(255,255,255,0.04)",
    isLight,
  };
}

function isLightColor(hex: string): boolean {
  // Simple luminance check
  const match = hex.match(/^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
  if (!match) return false;
  const r = parseInt(match[1], 16);
  const g = parseInt(match[2], 16);
  const b = parseInt(match[3], 16);
  return (r * 299 + g * 587 + b * 114) / 1000 < 128; // dark text = light theme
}
