import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface TEOAEScreenerData {
  frequency: number;
  amplitude: number;
  noiseFloor: number;
  snr: number;
  pass: boolean;
}

export interface TEOAEScreenerChartProps {
  data: TEOAEScreenerData[];
  reproducibility: number;
  ear: "right" | "left";
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

export function TEOAEScreenerChart({
  data,
  reproducibility,
  ear,
  width = 500,
  height = 250,
}: TEOAEScreenerChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const bands = data.map((d) => String(d.frequency));
    const x = d3.scaleBand().domain(bands).range([0, innerW]).padding(0.4);
    const dotY = innerH / 2;

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Center line
    g.append("line")
      .attr("x1", 0).attr("y1", dotY)
      .attr("x2", innerW).attr("y2", dotY)
      .attr("stroke", "rgba(255,255,255,0.05)");

    // Draw dots per frequency band
    data.forEach((d) => {
      const cx = (x(String(d.frequency)) || 0) + x.bandwidth() / 2;
      const color = d.pass ? "#22c55e" : "#ef4444";

      // Outer glow
      g.append("circle")
        .attr("cx", cx)
        .attr("cy", dotY)
        .attr("r", 16)
        .attr("fill", d.pass ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)");

      // Dot
      g.append("circle")
        .attr("cx", cx)
        .attr("cy", dotY)
        .attr("r", 10)
        .attr("fill", color)
        .attr("fill-opacity", 0.8);

      // Pass/Fail label
      g.append("text")
        .attr("x", cx)
        .attr("y", dotY + 1)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("fill", "white")
        .attr("font-size", 9)
        .attr("font-weight", "bold")
        .text(d.pass ? "P" : "F");

      // Frequency label below
      const freq = d.frequency;
      g.append("text")
        .attr("x", cx)
        .attr("y", dotY + 30)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(freq >= 1000 ? `${freq / 1000}k` : freq);

      // SNR value above
      g.append("text")
        .attr("x", cx)
        .attr("y", dotY - 22)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.3)")
        .attr("font-size", 9)
        .text(`${d.snr.toFixed(0)} dB`);
    });

    // Summary
    const passCount = data.filter((d) => d.pass).length;
    const overall = passCount >= Math.ceil(data.length * 0.7) && reproducibility >= 70;

    g.append("text")
      .attr("x", innerW / 2)
      .attr("y", innerH - 5)
      .attr("text-anchor", "middle")
      .attr("fill", overall ? "#22c55e" : "#ef4444")
      .attr("font-size", 11)
      .attr("font-weight", "bold")
      .text(overall ? "PASA" : "REFIERE");

    g.append("text")
      .attr("x", innerW / 2)
      .attr("y", innerH + 10)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 9)
      .text(`Reproducibilidad: ${reproducibility}%`);

    // Title
    const earLabel = ear === "right" ? "Oído Derecho" : "Oído Izquierdo";
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text(`TEOAE Screener - ${earLabel}`);

  }, [data, reproducibility, ear, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
