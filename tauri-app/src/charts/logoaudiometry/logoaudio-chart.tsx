import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface LogoaudioPoint {
  intensity: number;       // dB HL
  discrimination: number;  // 0-100%
  ear: "right" | "left";
}

interface LogoaudioChartProps {
  points: LogoaudioPoint[];
  srtRight?: number;
  srtLeft?: number;
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

export function LogoaudioChart({
  points,
  srtRight,
  srtLeft,
  width = 500,
  height = 350,
}: LogoaudioChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3.scaleLinear().domain([0, 120]).range([0, innerW]);
    const y = d3.scaleLinear().domain([0, 100]).range([innerH, 0]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Normal range shading
    g.append("rect")
      .attr("x", 0).attr("y", y(100))
      .attr("width", innerW).attr("height", y(88) - y(100))
      .attr("fill", "rgba(34, 197, 94, 0.04)");

    // Grid
    for (let db = 0; db <= 120; db += 20) {
      g.append("line")
        .attr("x1", x(db)).attr("y1", 0)
        .attr("x2", x(db)).attr("y2", innerH)
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", x(db)).attr("y", innerH + 18)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(db);
    }

    for (let pct = 0; pct <= 100; pct += 20) {
      g.append("line")
        .attr("x1", 0).attr("y1", y(pct))
        .attr("x2", innerW).attr("y2", y(pct))
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", -8).attr("y", y(pct))
        .attr("text-anchor", "end")
        .attr("dominant-baseline", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(`${pct}%`);
    }

    // 50% line (for SRT)
    g.append("line")
      .attr("x1", 0).attr("y1", y(50))
      .attr("x2", innerW).attr("y2", y(50))
      .attr("stroke", "rgba(255,255,255,0.15)")
      .attr("stroke-dasharray", "4,4");

    // Normal curve reference (sigmoid)
    const normalCurve: { intensity: number; discrimination: number }[] = [];
    for (let db = 0; db <= 120; db += 2) {
      const disc = 100 / (1 + Math.exp(-0.2 * (db - 25)));
      normalCurve.push({ intensity: db, discrimination: disc });
    }
    const normalLine = d3
      .line<{ intensity: number; discrimination: number }>()
      .x((d) => x(d.intensity))
      .y((d) => y(d.discrimination))
      .curve(d3.curveBasis);

    g.append("path")
      .datum(normalCurve)
      .attr("d", normalLine)
      .attr("fill", "none")
      .attr("stroke", "rgba(255,255,255,0.1)")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "6,3");

    // Draw data per ear
    ["right", "left"].forEach((ear) => {
      const earPoints = points
        .filter((p) => p.ear === ear)
        .sort((a, b) => a.intensity - b.intensity);

      if (earPoints.length === 0) return;

      const color = ear === "right" ? "#ef4444" : "#3b82f6";

      // Line
      const line = d3
        .line<LogoaudioPoint>()
        .x((d) => x(d.intensity))
        .y((d) => y(d.discrimination))
        .curve(d3.curveMonotoneX);

      g.append("path")
        .datum(earPoints)
        .attr("d", line)
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 2);

      // Points
      earPoints.forEach((p) => {
        if (ear === "right") {
          g.append("circle")
            .attr("cx", x(p.intensity)).attr("cy", y(p.discrimination)).attr("r", 4)
            .attr("fill", color);
        } else {
          g.append("rect")
            .attr("x", x(p.intensity) - 4).attr("y", y(p.discrimination) - 4)
            .attr("width", 8).attr("height", 8)
            .attr("fill", color);
        }
      });
    });

    // SRT markers
    [
      { srt: srtRight, color: "#ef4444", label: "SRT OD" },
      { srt: srtLeft, color: "#3b82f6", label: "SRT OI" },
    ].forEach(({ srt, color, label }) => {
      if (srt == null) return;
      g.append("line")
        .attr("x1", x(srt)).attr("y1", y(50) - 5)
        .attr("x2", x(srt)).attr("y2", y(50) + 5)
        .attr("stroke", color).attr("stroke-width", 2);
      g.append("text")
        .attr("x", x(srt)).attr("y", y(50) - 10)
        .attr("text-anchor", "middle")
        .attr("fill", color).attr("font-size", 9)
        .text(label);
    });

    // Axis labels
    g.append("text")
      .attr("x", innerW / 2).attr("y", innerH + 35)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Intensidad (dB HL)");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerH / 2).attr("y", -38)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Discriminación (%)");

    // Title
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text("Logoaudiometría");

  }, [points, srtRight, srtLeft, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
