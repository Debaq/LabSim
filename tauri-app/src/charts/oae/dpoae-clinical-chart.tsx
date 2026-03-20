import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface DPOAEData {
  frequency: number;    // Hz
  amplitude: number;    // dB SPL
  noiseFloor: number;   // dB SPL
  pass: boolean;
}

export interface DPOAEClinicalChartProps {
  data: DPOAEData[];
  ear: "right" | "left";
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

export function DPOAEClinicalChart({
  data,
  ear,
  width = 500,
  height = 350,
}: DPOAEClinicalChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const freqs = data.map((d) => d.frequency);
    const x = d3.scaleLog().domain([1000, 8000]).range([0, innerW]);
    const y = d3.scaleLinear().domain([-20, 30]).range([innerH, 0]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid horizontal
    for (let db = -20; db <= 30; db += 10) {
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

    // Grid vertical at test frequencies
    const tickFreqs = [1000, 1500, 2000, 3000, 4000, 6000, 8000];
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

    // SNR threshold line (~6 dB above noise conceptually shown as fixed line)
    g.append("line")
      .attr("x1", 0).attr("y1", y(6))
      .attr("x2", innerW).attr("y2", y(6))
      .attr("stroke", "rgba(255, 200, 50, 0.3)")
      .attr("stroke-width", 1)
      .attr("stroke-dasharray", "4,4");

    g.append("text")
      .attr("x", innerW - 4).attr("y", y(6) - 6)
      .attr("text-anchor", "end")
      .attr("fill", "rgba(255, 200, 50, 0.4)")
      .attr("font-size", 9)
      .text("Umbral SNR 6 dB");

    // Bars
    const barW = Math.min(20, (innerW / freqs.length) * 0.35);

    data.forEach((d) => {
      const cx = x(d.frequency);

      // Noise floor bar (gray)
      const nfHeight = y(-20) - y(d.noiseFloor);
      if (d.noiseFloor > -20) {
        g.append("rect")
          .attr("x", cx + 2)
          .attr("y", y(d.noiseFloor))
          .attr("width", barW)
          .attr("height", Math.max(0, nfHeight))
          .attr("fill", "rgba(255,255,255,0.15)")
          .attr("rx", 1);
      }

      // Amplitude bar (green if pass, red if fail)
      const ampHeight = y(-20) - y(d.amplitude);
      if (d.amplitude > -20) {
        g.append("rect")
          .attr("x", cx - barW - 2)
          .attr("y", y(d.amplitude))
          .attr("width", barW)
          .attr("height", Math.max(0, ampHeight))
          .attr("fill", d.pass ? "rgba(34, 197, 94, 0.7)" : "rgba(239, 68, 68, 0.7)")
          .attr("rx", 1);
      }

      // Pass/fail indicator
      g.append("text")
        .attr("x", cx)
        .attr("y", y(d.amplitude) - 8)
        .attr("text-anchor", "middle")
        .attr("fill", d.pass ? "#22c55e" : "#ef4444")
        .attr("font-size", 9)
        .attr("font-weight", "bold")
        .text(d.pass ? "P" : "F");
    });

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
      .text("Amplitud (dB SPL)");

    // Legend
    const legendY = -5;
    g.append("rect").attr("x", innerW - 110).attr("y", legendY).attr("width", 10).attr("height", 10).attr("fill", "rgba(34,197,94,0.7)");
    g.append("text").attr("x", innerW - 96).attr("y", legendY + 9).attr("fill", "rgba(255,255,255,0.4)").attr("font-size", 9).text("Señal");
    g.append("rect").attr("x", innerW - 55).attr("y", legendY).attr("width", 10).attr("height", 10).attr("fill", "rgba(255,255,255,0.15)");
    g.append("text").attr("x", innerW - 41).attr("y", legendY + 9).attr("fill", "rgba(255,255,255,0.4)").attr("font-size", 9).text("Ruido");

    // Title
    const earLabel = ear === "right" ? "Oído Derecho" : "Oído Izquierdo";
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text(`DPOAE Clínico - ${earLabel}`);

  }, [data, ear, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
