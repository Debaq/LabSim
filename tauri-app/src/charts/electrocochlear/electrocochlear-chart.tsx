import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface EcochgWaveformPoint {
  t: number;  // ms
  v: number;  // µV
}

export interface ElectrocochlearChartProps {
  waveform: EcochgWaveformPoint[];
  spLatency: number | null;   // ms, summating potential
  apLatency: number | null;   // ms, action potential
  ear: "right" | "left";
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

export function ElectrocochlearChart({
  waveform,
  spLatency,
  apLatency,
  ear,
  width = 500,
  height = 350,
}: ElectrocochlearChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3.scaleLinear().domain([0, 10]).range([0, innerW]);

    // Auto-scale Y based on waveform
    const yMin = d3.min(waveform, (d) => d.v) ?? -1;
    const yMax = d3.max(waveform, (d) => d.v) ?? 1;
    const yPad = (yMax - yMin) * 0.15;
    const y = d3.scaleLinear().domain([yMin - yPad, yMax + yPad]).range([innerH, 0]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid vertical
    for (let t = 0; t <= 10; t += 1) {
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
    const yStep = (yMax + yPad - (yMin - yPad)) / 5;
    for (let i = 0; i <= 5; i++) {
      const val = yMin - yPad + i * yStep;
      g.append("line")
        .attr("x1", 0).attr("y1", y(val))
        .attr("x2", innerW).attr("y2", y(val))
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", -8).attr("y", y(val))
        .attr("text-anchor", "end")
        .attr("dominant-baseline", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(val.toFixed(2));
    }

    // Zero line
    g.append("line")
      .attr("x1", 0).attr("y1", y(0))
      .attr("x2", innerW).attr("y2", y(0))
      .attr("stroke", "rgba(255,255,255,0.15)");

    // Waveform
    const color = ear === "right" ? "#ef4444" : "#3b82f6";
    const sorted = [...waveform].sort((a, b) => a.t - b.t);

    const line = d3
      .line<EcochgWaveformPoint>()
      .x((d) => x(d.t))
      .y((d) => y(d.v))
      .curve(d3.curveBasis);

    g.append("path")
      .datum(sorted)
      .attr("d", line)
      .attr("fill", "none")
      .attr("stroke", color)
      .attr("stroke-width", 1.5);

    // Find amplitude at latency using interpolation
    const findAmplitudeAt = (latency: number): number => {
      for (let i = 0; i < sorted.length - 1; i++) {
        if (sorted[i].t <= latency && sorted[i + 1].t >= latency) {
          const ratio = (latency - sorted[i].t) / (sorted[i + 1].t - sorted[i].t);
          return sorted[i].v + ratio * (sorted[i + 1].v - sorted[i].v);
        }
      }
      return 0;
    };

    // Mark SP peak
    let spAmplitude = 0;
    if (spLatency !== null) {
      spAmplitude = findAmplitudeAt(spLatency);

      g.append("circle")
        .attr("cx", x(spLatency))
        .attr("cy", y(spAmplitude))
        .attr("r", 5)
        .attr("fill", "none")
        .attr("stroke", "#f59e0b")
        .attr("stroke-width", 2);

      g.append("text")
        .attr("x", x(spLatency))
        .attr("y", y(spAmplitude) - 14)
        .attr("text-anchor", "middle")
        .attr("fill", "#f59e0b")
        .attr("font-size", 10)
        .attr("font-weight", "bold")
        .text("SP");

      g.append("text")
        .attr("x", x(spLatency))
        .attr("y", y(spAmplitude) - 4)
        .attr("text-anchor", "middle")
        .attr("fill", "#f59e0b")
        .attr("font-size", 8)
        .text(`${spLatency.toFixed(1)} ms`);
    }

    // Mark AP peak
    let apAmplitude = 0;
    if (apLatency !== null) {
      apAmplitude = findAmplitudeAt(apLatency);

      g.append("circle")
        .attr("cx", x(apLatency))
        .attr("cy", y(apAmplitude))
        .attr("r", 5)
        .attr("fill", "none")
        .attr("stroke", "#22c55e")
        .attr("stroke-width", 2);

      g.append("text")
        .attr("x", x(apLatency))
        .attr("y", y(apAmplitude) - 14)
        .attr("text-anchor", "middle")
        .attr("fill", "#22c55e")
        .attr("font-size", 10)
        .attr("font-weight", "bold")
        .text("AP");

      g.append("text")
        .attr("x", x(apLatency))
        .attr("y", y(apAmplitude) - 4)
        .attr("text-anchor", "middle")
        .attr("fill", "#22c55e")
        .attr("font-size", 8)
        .text(`${apLatency.toFixed(1)} ms`);
    }

    // SP/AP ratio display
    if (spLatency !== null && apLatency !== null && apAmplitude !== 0) {
      const ratio = Math.abs(spAmplitude / apAmplitude);
      const ratioColor = ratio > 0.4 ? "#ef4444" : "#22c55e";

      g.append("text")
        .attr("x", innerW)
        .attr("y", -5)
        .attr("text-anchor", "end")
        .attr("fill", ratioColor)
        .attr("font-size", 11)
        .attr("font-weight", "bold")
        .text(`SP/AP: ${ratio.toFixed(2)}`);

      g.append("text")
        .attr("x", innerW)
        .attr("y", 10)
        .attr("text-anchor", "end")
        .attr("fill", "rgba(255,255,255,0.3)")
        .attr("font-size", 9)
        .text(ratio > 0.4 ? "(Anormal > 0.4)" : "(Normal ≤ 0.4)");
    }

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

    // Title
    const earLabel = ear === "right" ? "Oído Derecho" : "Oído Izquierdo";
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text(`Electrococleografía - ${earLabel}`);

  }, [waveform, spLatency, apLatency, ear, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
