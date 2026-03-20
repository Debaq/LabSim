import { useRef, useEffect, useCallback, useState } from "react";
import * as d3 from "d3";
import { ISO_FREQUENCIES, THRESHOLD_MIN, THRESHOLD_MAX } from "@/lib/constants";

export interface AudiogramPoint {
  frequency: number;
  threshold: number;
  type: "air" | "bone";
  ear: "right" | "left";
  masked: boolean;
  noResponse?: boolean;
}

interface AudiogramChartProps {
  points: AudiogramPoint[];
  onPointAdd?: (point: AudiogramPoint) => void;
  onPointRemove?: (freq: number, ear: "right" | "left", type: "air" | "bone") => void;
  activeEar?: "right" | "left";
  activeType?: "air" | "bone";
  interactive?: boolean;
  width?: number;
  height?: number;
}

const MARGIN = { top: 30, right: 30, bottom: 40, left: 50 };

// Audiometric symbols - ISO 8253
const SYMBOLS = {
  air: {
    right: { shape: "circle", color: "#ef4444", fill: "none" },       // O rojo
    left: { shape: "cross", color: "#3b82f6", fill: "none" },         // X azul
  },
  bone: {
    right: { shape: "bracket-left", color: "#ef4444", fill: "none" }, // < rojo
    left: { shape: "bracket-right", color: "#3b82f6", fill: "none" }, // > azul
  },
  airMasked: {
    right: { shape: "triangle", color: "#ef4444", fill: "none" },     // △ rojo
    left: { shape: "square", color: "#3b82f6", fill: "none" },        // □ azul
  },
  boneMasked: {
    right: { shape: "bracket-left-m", color: "#ef4444", fill: "none" },
    left: { shape: "bracket-right-m", color: "#3b82f6", fill: "none" },
  },
};

function drawSymbol(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  x: number,
  y: number,
  point: AudiogramPoint,
  size: number = 8,
) {
  const category = point.masked
    ? point.type === "air" ? "airMasked" : "boneMasked"
    : point.type;
  const sym = SYMBOLS[category as keyof typeof SYMBOLS][point.ear];
  const color = sym.color;

  switch (sym.shape) {
    case "circle": // O - Right air unmasked
      g.append("circle")
        .attr("cx", x).attr("cy", y).attr("r", size)
        .attr("fill", "none").attr("stroke", color).attr("stroke-width", 2);
      break;

    case "cross": // X - Left air unmasked
      g.append("line")
        .attr("x1", x - size).attr("y1", y - size)
        .attr("x2", x + size).attr("y2", y + size)
        .attr("stroke", color).attr("stroke-width", 2);
      g.append("line")
        .attr("x1", x + size).attr("y1", y - size)
        .attr("x2", x - size).attr("y2", y + size)
        .attr("stroke", color).attr("stroke-width", 2);
      break;

    case "bracket-left": // < - Right bone unmasked
      g.append("polyline")
        .attr("points", `${x + size / 2},${y - size} ${x - size / 2},${y} ${x + size / 2},${y + size}`)
        .attr("fill", "none").attr("stroke", color).attr("stroke-width", 2);
      break;

    case "bracket-right": // > - Left bone unmasked
      g.append("polyline")
        .attr("points", `${x - size / 2},${y - size} ${x + size / 2},${y} ${x - size / 2},${y + size}`)
        .attr("fill", "none").attr("stroke", color).attr("stroke-width", 2);
      break;

    case "triangle": // △ - Right air masked
      g.append("polygon")
        .attr("points", `${x},${y - size} ${x - size},${y + size} ${x + size},${y + size}`)
        .attr("fill", "none").attr("stroke", color).attr("stroke-width", 2);
      break;

    case "square": // □ - Left air masked
      g.append("rect")
        .attr("x", x - size).attr("y", y - size)
        .attr("width", size * 2).attr("height", size * 2)
        .attr("fill", "none").attr("stroke", color).attr("stroke-width", 2);
      break;

    case "bracket-left-m": // [ - Right bone masked
      g.append("polyline")
        .attr("points", `${x + size / 2},${y - size} ${x - size / 2},${y - size} ${x - size / 2},${y + size} ${x + size / 2},${y + size}`)
        .attr("fill", "none").attr("stroke", color).attr("stroke-width", 2);
      break;

    case "bracket-right-m": // ] - Left bone masked
      g.append("polyline")
        .attr("points", `${x - size / 2},${y - size} ${x + size / 2},${y - size} ${x + size / 2},${y + size} ${x - size / 2},${y + size}`)
        .attr("fill", "none").attr("stroke", color).attr("stroke-width", 2);
      break;
  }

  // No response arrow
  if (point.noResponse) {
    g.append("line")
      .attr("x1", x + size).attr("y1", y + size)
      .attr("x2", x + size + 6).attr("y2", y + size + 8)
      .attr("stroke", color).attr("stroke-width", 1.5)
      .attr("marker-end", `url(#arrow-${point.ear})`);
  }
}

export function AudiogramChart({
  points,
  onPointAdd,
  onPointRemove,
  activeEar = "right",
  activeType = "air",
  interactive = true,
  width: propWidth,
  height: propHeight,
}: AudiogramChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: propWidth ?? 600, height: propHeight ?? 450 });

  // Responsive resize
  useEffect(() => {
    if (propWidth && propHeight) return;
    const container = containerRef.current;
    if (!container) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setDimensions({
          width: propWidth ?? Math.max(400, width),
          height: propHeight ?? Math.max(300, height),
        });
      }
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, [propWidth, propHeight]);

  const { width, height } = dimensions;
  const innerW = width - MARGIN.left - MARGIN.right;
  const innerH = height - MARGIN.top - MARGIN.bottom;

  // Scales
  const xScale = useCallback(
    () =>
      d3
        .scaleLog()
        .domain([125, 8000])
        .range([0, innerW]),
    [innerW],
  );

  const yScale = useCallback(
    () =>
      d3
        .scaleLinear()
        .domain([THRESHOLD_MIN, THRESHOLD_MAX])
        .range([0, innerH]),
    [innerH],
  );

  // Draw chart
  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const x = xScale();
    const y = yScale();

    // Defs (arrow markers)
    const defs = svg.append("defs");
    ["right", "left"].forEach((ear) => {
      defs
        .append("marker")
        .attr("id", `arrow-${ear}`)
        .attr("viewBox", "0 0 10 10")
        .attr("refX", 5).attr("refY", 5)
        .attr("markerWidth", 5).attr("markerHeight", 5)
        .attr("orient", "auto-start-reverse")
        .append("path")
        .attr("d", "M 0 0 L 10 5 L 0 10 z")
        .attr("fill", ear === "right" ? "#ef4444" : "#3b82f6");
    });

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Background zones
    // Normal hearing zone (0-20 dB)
    g.append("rect")
      .attr("x", 0).attr("y", y(0))
      .attr("width", innerW).attr("height", y(20) - y(0))
      .attr("fill", "rgba(34, 197, 94, 0.05)");

    // Grid - horizontal lines
    for (let db = THRESHOLD_MIN; db <= THRESHOLD_MAX; db += 10) {
      const isMainLine = db % 20 === 0;
      g.append("line")
        .attr("x1", 0).attr("y1", y(db))
        .attr("x2", innerW).attr("y2", y(db))
        .attr("stroke", isMainLine ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.04)")
        .attr("stroke-width", isMainLine ? 1 : 0.5);

      // Y-axis labels
      if (db % 20 === 0) {
        g.append("text")
          .attr("x", -8).attr("y", y(db))
          .attr("text-anchor", "end")
          .attr("dominant-baseline", "middle")
          .attr("fill", "rgba(255,255,255,0.4)")
          .attr("font-size", 10)
          .text(db);
      }
    }

    // Grid - vertical lines at frequencies
    ISO_FREQUENCIES.forEach((freq) => {
      g.append("line")
        .attr("x1", x(freq)).attr("y1", 0)
        .attr("x2", x(freq)).attr("y2", innerH)
        .attr("stroke", "rgba(255,255,255,0.06)")
        .attr("stroke-width", freq === 1000 || freq === 4000 ? 1 : 0.5);

      // X-axis labels
      g.append("text")
        .attr("x", x(freq)).attr("y", innerH + 20)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(freq >= 1000 ? `${freq / 1000}k` : freq);
    });

    // Axis labels
    g.append("text")
      .attr("x", innerW / 2).attr("y", innerH + 36)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Frecuencia (Hz)");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerH / 2).attr("y", -38)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Nivel auditivo (dB HL)");

    // Connect points with lines (per ear + type)
    const groups = d3.group(points, (p) => `${p.ear}-${p.type}-${p.masked}`);
    groups.forEach((pts) => {
      const sorted = [...pts].sort((a, b) => a.frequency - b.frequency);
      if (sorted.length < 2) return;

      const lineGen = d3
        .line<AudiogramPoint>()
        .x((d) => x(d.frequency))
        .y((d) => y(d.threshold))
        .curve(d3.curveLinear);

      const ear = sorted[0].ear;
      g.append("path")
        .datum(sorted)
        .attr("d", lineGen)
        .attr("fill", "none")
        .attr("stroke", ear === "right" ? "#ef4444" : "#3b82f6")
        .attr("stroke-width", 1.5)
        .attr("stroke-opacity", 0.6);
    });

    // Draw symbols
    const symbolsG = g.append("g").attr("class", "symbols");
    points.forEach((point) => {
      drawSymbol(
        symbolsG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>,
        x(point.frequency),
        y(point.threshold),
        point,
      );
    });

    // Interactive click to add/remove points
    if (interactive && onPointAdd) {
      g.append("rect")
        .attr("width", innerW).attr("height", innerH)
        .attr("fill", "transparent")
        .attr("cursor", "crosshair")
        .on("click", (event: MouseEvent) => {
          const [mx, my] = d3.pointer(event);
          const freq = x.invert(mx);
          const threshold = y.invert(my);

          // Snap to nearest ISO frequency
          const snappedFreq = ISO_FREQUENCIES.reduce((prev, curr) =>
            Math.abs(Math.log(curr) - Math.log(freq)) <
            Math.abs(Math.log(prev) - Math.log(freq))
              ? curr
              : prev,
          );

          // Snap to 5 dB steps
          const snappedThreshold = Math.round(threshold / 5) * 5;

          // Check if point already exists
          const existing = points.find(
            (p) =>
              p.frequency === snappedFreq &&
              p.ear === activeEar &&
              p.type === activeType,
          );

          if (existing && onPointRemove) {
            onPointRemove(snappedFreq, activeEar, activeType);
          } else {
            onPointAdd({
              frequency: snappedFreq,
              threshold: snappedThreshold,
              ear: activeEar,
              type: activeType,
              masked: false,
            });
          }
        });
    }

    // Legend
    const legend = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left + 10}, 14)`);

    // Right ear legend
    legend.append("circle")
      .attr("cx", 0).attr("cy", 0).attr("r", 5)
      .attr("fill", "none").attr("stroke", "#ef4444").attr("stroke-width", 1.5);
    legend.append("text")
      .attr("x", 10).attr("y", 4)
      .attr("fill", "rgba(255,255,255,0.5)").attr("font-size", 10)
      .text("OD (Derecho)");

    // Left ear legend
    legend.append("line")
      .attr("x1", 100 - 5).attr("y1", -5)
      .attr("x2", 100 + 5).attr("y2", 5)
      .attr("stroke", "#3b82f6").attr("stroke-width", 1.5);
    legend.append("line")
      .attr("x1", 100 + 5).attr("y1", -5)
      .attr("x2", 100 - 5).attr("y2", 5)
      .attr("stroke", "#3b82f6").attr("stroke-width", 1.5);
    legend.append("text")
      .attr("x", 110).attr("y", 4)
      .attr("fill", "rgba(255,255,255,0.5)").attr("font-size", 10)
      .text("OI (Izquierdo)");

  }, [points, activeEar, activeType, interactive, onPointAdd, onPointRemove, width, height, innerW, innerH, xScale, yScale]);

  return (
    <div ref={containerRef} className="h-full w-full">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="select-none"
      />
    </div>
  );
}
