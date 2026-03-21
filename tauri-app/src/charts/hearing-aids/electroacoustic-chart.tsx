import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface ElectroacousticData {
  freq: number;
  gain: number;
}

export interface ElectroacousticChartProps {
  data: ElectroacousticData[];
  ospl90?: ElectroacousticData[];  // optional OSPL90 curve
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

export function ElectroacousticChart({
  data,
  ospl90,
  width = 500,
  height = 350,
}: ElectroacousticChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3.scaleLog().domain([100, 10000]).range([0, innerW]);
    const y = d3.scaleLinear().domain([0, 80]).range([innerH, 0]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid vertical at audiometric frequencies
    const tickFreqs = [100, 200, 500, 1000, 2000, 4000, 8000, 10000];
    tickFreqs.forEach((f) => {
      g.append("line")
        .attr("x1", x(f)).attr("y1", 0)
        .attr("x2", x(f)).attr("y2", innerH)
        .attr("stroke", "rgba(255,255,255,0.05)");

      let label: string;
      if (f >= 1000) {
        label = `${f / 1000}k`;
      } else {
        label = String(f);
      }
      g.append("text")
        .attr("x", x(f)).attr("y", innerH + 18)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(label);
    });

    // Grid horizontal
    for (let db = 0; db <= 80; db += 10) {
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

    // Frequency response curve
    const sorted = [...data].sort((a, b) => a.freq - b.freq);
    const line = d3
      .line<ElectroacousticData>()
      .x((d) => x(d.freq))
      .y((d) => y(d.gain))
      .curve(d3.curveMonotoneX);

    g.append("path")
      .datum(sorted)
      .attr("d", line)
      .attr("fill", "none")
      .attr("stroke", "#3b82f6")
      .attr("stroke-width", 2);

    // OSPL90 reference line
    if (ospl90 && ospl90.length > 0) {
      const osplSorted = [...ospl90].sort((a, b) => a.freq - b.freq);
      const osplLine = d3
        .line<ElectroacousticData>()
        .x((d) => x(d.freq))
        .y((d) => y(d.gain))
        .curve(d3.curveMonotoneX);

      g.append("path")
        .datum(osplSorted)
        .attr("d", osplLine)
        .attr("fill", "none")
        .attr("stroke", "#ef4444")
        .attr("stroke-width", 1.5)
        .attr("stroke-dasharray", "5,3");

      // Legend for OSPL90
      g.append("line")
        .attr("x1", innerW - 100).attr("y1", -5)
        .attr("x2", innerW - 80).attr("y2", -5)
        .attr("stroke", "#ef4444")
        .attr("stroke-dasharray", "5,3")
        .attr("stroke-width", 1.5);
      g.append("text")
        .attr("x", innerW - 76).attr("y", -2)
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 9)
        .text("OSPL90");
    }

    // Legend for response
    g.append("line")
      .attr("x1", 0).attr("y1", -5)
      .attr("x2", 20).attr("y2", -5)
      .attr("stroke", "#3b82f6")
      .attr("stroke-width", 2);
    g.append("text")
      .attr("x", 24).attr("y", -2)
      .attr("fill", "rgba(255,255,255,0.4)")
      .attr("font-size", 9)
      .text("Resp. frecuencia");

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
      .text("Ganancia (dB)");

    // Title
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text("Análisis Electroacústico");

  }, [data, ospl90, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
