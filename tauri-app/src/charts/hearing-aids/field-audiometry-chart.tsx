import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface FieldAudiometryPoint {
  freq: number;
  threshold: number;
}

export interface FieldAudiometryChartProps {
  withoutAids: FieldAudiometryPoint[];
  withAids: FieldAudiometryPoint[];
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

// Speech banana approximate region (simplified)
const SPEECH_BANANA = [
  { freq: 250, upper: 20, lower: 55 },
  { freq: 500, upper: 15, lower: 50 },
  { freq: 1000, upper: 10, lower: 45 },
  { freq: 2000, upper: 10, lower: 50 },
  { freq: 4000, upper: 15, lower: 55 },
  { freq: 6000, upper: 20, lower: 55 },
  { freq: 8000, upper: 25, lower: 55 },
];

export function FieldAudiometryChart({
  withoutAids,
  withAids,
  width = 500,
  height = 350,
}: FieldAudiometryChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3.scaleLog().domain([250, 8000]).range([0, innerW]);
    const y = d3.scaleLinear().domain([-10, 120]).range([0, innerH]); // Inverted like audiogram

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid vertical
    const tickFreqs = [250, 500, 1000, 2000, 4000, 8000];
    tickFreqs.forEach((f) => {
      g.append("line")
        .attr("x1", x(f)).attr("y1", 0)
        .attr("x2", x(f)).attr("y2", innerH)
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", x(f)).attr("y", innerH + 18)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(f >= 1000 ? `${f / 1000}k` : f);
    });

    // Grid horizontal
    for (let db = -10; db <= 120; db += 10) {
      g.append("line")
        .attr("x1", 0).attr("y1", y(db))
        .attr("x2", innerW).attr("y2", y(db))
        .attr("stroke", "rgba(255,255,255,0.05)");
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

    // Speech banana shaded area
    const bananaArea = d3.area<{ freq: number; upper: number; lower: number }>()
      .x((d) => x(d.freq))
      .y0((d) => y(d.upper))
      .y1((d) => y(d.lower))
      .curve(d3.curveMonotoneX);

    g.append("path")
      .datum(SPEECH_BANANA)
      .attr("d", bananaArea)
      .attr("fill", "rgba(251, 191, 36, 0.06)")
      .attr("stroke", "rgba(251, 191, 36, 0.15)")
      .attr("stroke-width", 1);

    g.append("text")
      .attr("x", x(1000))
      .attr("y", y(35))
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(251, 191, 36, 0.25)")
      .attr("font-size", 9)
      .text("Zona del habla");

    // Functional gain area (between curves)
    const sortedWithout = [...withoutAids].sort((a, b) => a.freq - b.freq);
    const sortedWith = [...withAids].sort((a, b) => a.freq - b.freq);

    // Find common frequencies for area fill
    const commonFreqs = sortedWithout
      .filter((wo) => sortedWith.some((w) => w.freq === wo.freq))
      .map((wo) => {
        const w = sortedWith.find((w) => w.freq === wo.freq)!;
        return { freq: wo.freq, without: wo.threshold, with: w.threshold };
      });

    if (commonFreqs.length > 1) {
      const gainArea = d3.area<{ freq: number; without: number; with: number }>()
        .x((d) => x(d.freq))
        .y0((d) => y(d.without))
        .y1((d) => y(d.with))
        .curve(d3.curveMonotoneX);

      g.append("path")
        .datum(commonFreqs)
        .attr("d", gainArea)
        .attr("fill", "rgba(34, 197, 94, 0.08)");
    }

    // Without aids curve (dashed)
    const lineWithout = d3
      .line<FieldAudiometryPoint>()
      .x((d) => x(d.freq))
      .y((d) => y(d.threshold))
      .curve(d3.curveMonotoneX);

    g.append("path")
      .datum(sortedWithout)
      .attr("d", lineWithout)
      .attr("fill", "none")
      .attr("stroke", "#ef4444")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "6,3");

    sortedWithout.forEach((d) => {
      g.append("circle")
        .attr("cx", x(d.freq))
        .attr("cy", y(d.threshold))
        .attr("r", 4)
        .attr("fill", "#ef4444")
        .attr("fill-opacity", 0.8);
    });

    // With aids curve (solid)
    const lineWith = d3
      .line<FieldAudiometryPoint>()
      .x((d) => x(d.freq))
      .y((d) => y(d.threshold))
      .curve(d3.curveMonotoneX);

    g.append("path")
      .datum(sortedWith)
      .attr("d", lineWith)
      .attr("fill", "none")
      .attr("stroke", "#22c55e")
      .attr("stroke-width", 2);

    sortedWith.forEach((d) => {
      g.append("circle")
        .attr("cx", x(d.freq))
        .attr("cy", y(d.threshold))
        .attr("r", 4)
        .attr("fill", "#22c55e")
        .attr("fill-opacity", 0.8);
    });

    // Legend
    const legendY = -5;
    g.append("line").attr("x1", 0).attr("y1", legendY).attr("x2", 20).attr("y2", legendY)
      .attr("stroke", "#ef4444").attr("stroke-width", 2).attr("stroke-dasharray", "6,3");
    g.append("text").attr("x", 24).attr("y", legendY + 3).attr("fill", "rgba(255,255,255,0.4)").attr("font-size", 9).text("Sin audífonos");

    g.append("line").attr("x1", 110).attr("y1", legendY).attr("x2", 130).attr("y2", legendY)
      .attr("stroke", "#22c55e").attr("stroke-width", 2);
    g.append("text").attr("x", 134).attr("y", legendY + 3).attr("fill", "rgba(255,255,255,0.4)").attr("font-size", 9).text("Con audífonos");

    // Axis labels
    g.append("text")
      .attr("x", innerW / 2).attr("y", innerH + 35)
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
      .text("Umbral (dB HL)");

    // Title
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text("Audiometría en Campo Libre");

  }, [withoutAids, withAids, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
