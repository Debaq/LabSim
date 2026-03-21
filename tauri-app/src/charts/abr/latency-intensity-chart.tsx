import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface LatencyIntensityData {
  intensity: number;  // dB nHL
  latencyV: number;   // ms
  ear: "right" | "left";
}

export interface LatencyIntensityChartProps {
  data: LatencyIntensityData[];
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

// Normal latency-intensity range for wave V
const NORMAL_RANGE = [
  { intensity: 20, latMin: 7.0, latMax: 8.0 },
  { intensity: 30, latMin: 6.6, latMax: 7.6 },
  { intensity: 40, latMin: 6.2, latMax: 7.2 },
  { intensity: 50, latMin: 5.9, latMax: 6.8 },
  { intensity: 60, latMin: 5.6, latMax: 6.4 },
  { intensity: 70, latMin: 5.4, latMax: 6.1 },
  { intensity: 80, latMin: 5.2, latMax: 5.9 },
  { intensity: 90, latMin: 5.1, latMax: 5.7 },
  { intensity: 100, latMin: 5.0, latMax: 5.6 },
];

export function LatencyIntensityChart({
  data,
  width = 500,
  height = 350,
}: LatencyIntensityChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3.scaleLinear().domain([0, 100]).range([0, innerW]);
    const y = d3.scaleLinear().domain([8, 4]).range([innerH, 0]); // Inverted

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid vertical
    for (let i = 0; i <= 100; i += 10) {
      g.append("line")
        .attr("x1", x(i)).attr("y1", 0)
        .attr("x2", x(i)).attr("y2", innerH)
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", x(i)).attr("y", innerH + 18)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(i);
    }

    // Grid horizontal
    for (let l = 4; l <= 8; l += 0.5) {
      g.append("line")
        .attr("x1", 0).attr("y1", y(l))
        .attr("x2", innerW).attr("y2", y(l))
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", -8).attr("y", y(l))
        .attr("text-anchor", "end")
        .attr("dominant-baseline", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(l.toFixed(1));
    }

    // Normal range shading
    const areaGen = d3.area<{ intensity: number; latMin: number; latMax: number }>()
      .x((d) => x(d.intensity))
      .y0((d) => y(d.latMin))
      .y1((d) => y(d.latMax))
      .curve(d3.curveMonotoneX);

    g.append("path")
      .datum(NORMAL_RANGE)
      .attr("d", areaGen)
      .attr("fill", "rgba(34, 197, 94, 0.08)")
      .attr("stroke", "rgba(34, 197, 94, 0.2)")
      .attr("stroke-width", 1);

    g.append("text")
      .attr("x", x(85))
      .attr("y", y(5.4))
      .attr("fill", "rgba(34, 197, 94, 0.3)")
      .attr("font-size", 9)
      .text("Rango normal");

    // Axis labels
    g.append("text")
      .attr("x", innerW / 2).attr("y", innerH + 35)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Intensidad (dB nHL)");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerH / 2).attr("y", -38)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Latencia onda V (ms)");

    // Group data by ear
    const rightData = data.filter((d) => d.ear === "right").sort((a, b) => a.intensity - b.intensity);
    const leftData = data.filter((d) => d.ear === "left").sort((a, b) => a.intensity - b.intensity);

    const drawCurve = (earData: LatencyIntensityData[], color: string) => {
      if (earData.length === 0) return;

      const line = d3
        .line<LatencyIntensityData>()
        .x((d) => x(d.intensity))
        .y((d) => y(d.latencyV))
        .curve(d3.curveMonotoneX);

      g.append("path")
        .datum(earData)
        .attr("d", line)
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 2);

      earData.forEach((d) => {
        g.append("circle")
          .attr("cx", x(d.intensity))
          .attr("cy", y(d.latencyV))
          .attr("r", 4)
          .attr("fill", color)
          .attr("fill-opacity", 0.8);
      });
    };

    drawCurve(rightData, "#ef4444");
    drawCurve(leftData, "#3b82f6");

    // Title
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text("Curva Latencia-Intensidad");

  }, [data, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
