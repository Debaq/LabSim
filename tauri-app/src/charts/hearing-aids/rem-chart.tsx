import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface REMPoint {
  freq: number;
  db: number;
}

export interface REMChartProps {
  measured: REMPoint[];
  target: REMPoint[];
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

export function REMChart({
  measured,
  target,
  width = 500,
  height = 350,
}: REMChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3.scaleLog().domain([200, 8000]).range([0, innerW]);
    const y = d3.scaleLinear().domain([40, 100]).range([innerH, 0]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid vertical
    const tickFreqs = [200, 500, 1000, 2000, 4000, 8000];
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
    for (let db = 40; db <= 100; db += 10) {
      g.append("line")
        .attr("x1", 0).attr("y1", y(db))
        .attr("x2", innerW).attr("y2", y(db))
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", -8).attr("y", y(db))
        .attr("text-anchor", "end")
        .attr("dominant-baseline", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(db);
    }

    const sortedTarget = [...target].sort((a, b) => a.freq - b.freq);
    const sortedMeasured = [...measured].sort((a, b) => a.freq - b.freq);

    // Difference highlight area between measured and target
    const commonFreqs = sortedMeasured
      .filter((m) => sortedTarget.some((t) => t.freq === m.freq))
      .map((m) => {
        const t = sortedTarget.find((t) => t.freq === m.freq)!;
        return { freq: m.freq, measured: m.db, target: t.db };
      });

    if (commonFreqs.length > 1) {
      const diffArea = d3.area<{ freq: number; measured: number; target: number }>()
        .x((d) => x(d.freq))
        .y0((d) => y(d.target))
        .y1((d) => y(d.measured))
        .curve(d3.curveMonotoneX);

      g.append("path")
        .datum(commonFreqs)
        .attr("d", diffArea)
        .attr("fill", "rgba(251, 191, 36, 0.08)");
    }

    // Target curve (dashed)
    const targetLine = d3
      .line<REMPoint>()
      .x((d) => x(d.freq))
      .y((d) => y(d.db))
      .curve(d3.curveMonotoneX);

    g.append("path")
      .datum(sortedTarget)
      .attr("d", targetLine)
      .attr("fill", "none")
      .attr("stroke", "rgba(255,255,255,0.5)")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "6,3");

    // Measured curve (solid)
    const measuredLine = d3
      .line<REMPoint>()
      .x((d) => x(d.freq))
      .y((d) => y(d.db))
      .curve(d3.curveMonotoneX);

    g.append("path")
      .datum(sortedMeasured)
      .attr("d", measuredLine)
      .attr("fill", "none")
      .attr("stroke", "#3b82f6")
      .attr("stroke-width", 2);

    sortedMeasured.forEach((d) => {
      g.append("circle")
        .attr("cx", x(d.freq))
        .attr("cy", y(d.db))
        .attr("r", 3)
        .attr("fill", "#3b82f6");
    });

    // Legend
    const legendY = -5;
    g.append("line").attr("x1", 0).attr("y1", legendY).attr("x2", 20).attr("y2", legendY)
      .attr("stroke", "rgba(255,255,255,0.5)").attr("stroke-width", 2).attr("stroke-dasharray", "6,3");
    g.append("text").attr("x", 24).attr("y", legendY + 3).attr("fill", "rgba(255,255,255,0.4)").attr("font-size", 9).text("Objetivo");

    g.append("line").attr("x1", 90).attr("y1", legendY).attr("x2", 110).attr("y2", legendY)
      .attr("stroke", "#3b82f6").attr("stroke-width", 2);
    g.append("text").attr("x", 114).attr("y", legendY + 3).attr("fill", "rgba(255,255,255,0.4)").attr("font-size", 9).text("Medido");

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
      .text("NPS (dB SPL)");

    // Title
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text("Medición en Oído Real (REM)");

  }, [measured, target, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
