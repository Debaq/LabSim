import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface TEOAEData {
  frequency: number;    // Hz band center
  amplitude: number;    // dB SPL
  noiseFloor: number;   // dB SPL
  snr: number;          // dB
  pass: boolean;
}

export interface TEOAEClinicalChartProps {
  data: TEOAEData[];
  reproducibility: number; // 0-100%
  ear: "right" | "left";
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

export function TEOAEClinicalChart({
  data,
  reproducibility,
  ear,
  width = 500,
  height = 350,
}: TEOAEClinicalChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const bands = data.map((d) => String(d.frequency));
    const x = d3.scaleBand().domain(bands).range([0, innerW]).padding(0.3);
    const y = d3.scaleLinear().domain([-10, 30]).range([innerH, 0]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid horizontal
    for (let db = -10; db <= 30; db += 5) {
      g.append("line")
        .attr("x1", 0).attr("y1", y(db))
        .attr("x2", innerW).attr("y2", y(db))
        .attr("stroke", "rgba(255,255,255,0.05)");
      if (db % 10 === 0) {
        g.append("text")
          .attr("x", -8).attr("y", y(db))
          .attr("text-anchor", "end")
          .attr("dominant-baseline", "middle")
          .attr("fill", "rgba(255,255,255,0.4)")
          .attr("font-size", 10)
          .text(db);
      }
    }

    // Frequency labels
    bands.forEach((b) => {
      const freq = parseInt(b);
      g.append("text")
        .attr("x", (x(b) || 0) + x.bandwidth() / 2)
        .attr("y", innerH + 18)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(freq >= 1000 ? `${freq / 1000}k` : freq);
    });

    // Paired bars per band
    const halfBar = x.bandwidth() / 2 - 2;

    data.forEach((d) => {
      const bx = x(String(d.frequency)) || 0;

      // Signal bar (left half)
      const sigH = y(-10) - y(d.amplitude);
      if (d.amplitude > -10) {
        g.append("rect")
          .attr("x", bx)
          .attr("y", y(d.amplitude))
          .attr("width", halfBar)
          .attr("height", Math.max(0, sigH))
          .attr("fill", d.pass ? "rgba(34,197,94,0.7)" : "rgba(239,68,68,0.7)")
          .attr("rx", 1);
      }

      // Noise bar (right half)
      const noiseH = y(-10) - y(d.noiseFloor);
      if (d.noiseFloor > -10) {
        g.append("rect")
          .attr("x", bx + halfBar + 4)
          .attr("y", y(d.noiseFloor))
          .attr("width", halfBar)
          .attr("height", Math.max(0, noiseH))
          .attr("fill", "rgba(255,255,255,0.15)")
          .attr("rx", 1);
      }

      // SNR label above
      g.append("text")
        .attr("x", bx + x.bandwidth() / 2)
        .attr("y", y(Math.max(d.amplitude, d.noiseFloor)) - 8)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.3)")
        .attr("font-size", 8)
        .text(`SNR: ${d.snr.toFixed(1)}`);
    });

    // Axis labels
    g.append("text")
      .attr("x", innerW / 2).attr("y", innerH + 35)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Banda de frecuencia (Hz)");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerH / 2).attr("y", -38)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Amplitud (dB SPL)");

    // Reproducibility display
    const reproColor = reproducibility >= 70 ? "#22c55e" : "#ef4444";
    g.append("text")
      .attr("x", innerW)
      .attr("y", -5)
      .attr("text-anchor", "end")
      .attr("fill", reproColor)
      .attr("font-size", 11)
      .attr("font-weight", "bold")
      .text(`Reproducibilidad: ${reproducibility}%`);

    // Legend
    const legendY = -5;
    g.append("rect").attr("x", 0).attr("y", legendY).attr("width", 10).attr("height", 10).attr("fill", "rgba(34,197,94,0.7)");
    g.append("text").attr("x", 14).attr("y", legendY + 9).attr("fill", "rgba(255,255,255,0.4)").attr("font-size", 9).text("Señal");
    g.append("rect").attr("x", 50).attr("y", legendY).attr("width", 10).attr("height", 10).attr("fill", "rgba(255,255,255,0.15)");
    g.append("text").attr("x", 64).attr("y", legendY + 9).attr("fill", "rgba(255,255,255,0.4)").attr("font-size", 9).text("Ruido");

    // Title
    const earLabel = ear === "right" ? "Oído Derecho" : "Oído Izquierdo";
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text(`TEOAE Clínico - ${earLabel}`);

  }, [data, reproducibility, ear, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
