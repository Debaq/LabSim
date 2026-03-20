import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface WaveData {
  onda: string;       // "I", "III", "V"
  latencia: number;   // ms
  amplitud: number;   // µV
  presente: boolean;
}

export interface WaveformChartProps {
  waves: WaveData[];
  ear: "right" | "left";
  intensity: string;  // "80dB", "final", etc.
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

function generateWaveform(
  waves: WaveData[],
  timeRange: [number, number],
): { t: number; v: number }[] {
  const points: { t: number; v: number }[] = [];
  const dt = 0.02;

  for (let t = timeRange[0]; t <= timeRange[1]; t += dt) {
    let v = 0;
    // Base noise
    v += (Math.random() - 0.5) * 0.05;

    // Add wave peaks for each present wave
    for (const w of waves) {
      if (!w.presente) continue;
      const sigma = 0.3;
      const dist = t - w.latencia;
      // Bifasic waveform: positive peak followed by negative trough
      const positive = w.amplitud * Math.exp(-Math.pow(dist, 2) / (2 * sigma * sigma));
      const negative = -w.amplitud * 0.6 * Math.exp(-Math.pow(dist - sigma * 1.2, 2) / (2 * sigma * sigma));
      v += positive + negative;
    }

    points.push({ t, v });
  }

  return points;
}

export function WaveformChart({
  waves,
  ear,
  intensity,
  width = 500,
  height = 350,
}: WaveformChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3.scaleLinear().domain([0, 12]).range([0, innerW]);
    const y = d3.scaleLinear().domain([-2, 2]).range([innerH, 0]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid vertical
    for (let t = 0; t <= 12; t += 1) {
      g.append("line")
        .attr("x1", x(t)).attr("y1", 0)
        .attr("x2", x(t)).attr("y2", innerH)
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", x(t)).attr("y", innerH + 18)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(t);
    }

    // Grid horizontal
    for (let v = -2; v <= 2; v += 0.5) {
      g.append("line")
        .attr("x1", 0).attr("y1", y(v))
        .attr("x2", innerW).attr("y2", y(v))
        .attr("stroke", "rgba(255,255,255,0.05)");
      if (Number.isInteger(v) || v === -0.5 || v === 0.5 || v === 1.5 || v === -1.5) {
        g.append("text")
          .attr("x", -8).attr("y", y(v))
          .attr("text-anchor", "end")
          .attr("dominant-baseline", "middle")
          .attr("fill", "rgba(255,255,255,0.4)")
          .attr("font-size", 10)
          .text(v.toFixed(1));
      }
    }

    // Zero line
    g.append("line")
      .attr("x1", 0).attr("y1", y(0))
      .attr("x2", innerW).attr("y2", y(0))
      .attr("stroke", "rgba(255,255,255,0.15)");

    // Axis labels
    g.append("text")
      .attr("x", innerW / 2).attr("y", innerH + 35)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Tiempo (ms)");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerH / 2).attr("y", -38)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Amplitud (µV)");

    // Generate and draw waveform
    const color = ear === "right" ? "#ef4444" : "#3b82f6";
    const waveformData = generateWaveform(waves, [0, 12]);

    const line = d3
      .line<{ t: number; v: number }>()
      .x((d) => x(d.t))
      .y((d) => y(d.v))
      .curve(d3.curveBasis);

    g.append("path")
      .datum(waveformData)
      .attr("d", line)
      .attr("fill", "none")
      .attr("stroke", color)
      .attr("stroke-width", 1.5);

    // Mark peaks
    waves.forEach((w) => {
      if (!w.presente) return;

      g.append("circle")
        .attr("cx", x(w.latencia))
        .attr("cy", y(w.amplitud))
        .attr("r", 4)
        .attr("fill", color)
        .attr("fill-opacity", 0.8);

      g.append("text")
        .attr("x", x(w.latencia))
        .attr("y", y(w.amplitud) - 12)
        .attr("text-anchor", "middle")
        .attr("fill", color)
        .attr("font-size", 10)
        .attr("font-weight", "bold")
        .text(w.onda);
    });

    // Title
    const earLabel = ear === "right" ? "Oído Derecho" : "Oído Izquierdo";
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text(`PEATC - ${earLabel} (${intensity})`);

  }, [waves, ear, intensity, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
