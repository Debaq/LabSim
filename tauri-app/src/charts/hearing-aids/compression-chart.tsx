import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface CompressionChartProps {
  curves: { inputDb: number; outputDb: number }[];
  kneePoint: number;   // dB
  ratio: string;       // e.g. "2:1"
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

export function CompressionChart({
  curves,
  kneePoint,
  ratio,
  width = 500,
  height = 350,
}: CompressionChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3.scaleLinear().domain([0, 100]).range([0, innerW]);
    const y = d3.scaleLinear().domain([0, 140]).range([innerH, 0]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid
    for (let v = 0; v <= 100; v += 10) {
      g.append("line")
        .attr("x1", x(v)).attr("y1", 0)
        .attr("x2", x(v)).attr("y2", innerH)
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", x(v)).attr("y", innerH + 18)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(v);
    }

    for (let v = 0; v <= 140; v += 20) {
      g.append("line")
        .attr("x1", 0).attr("y1", y(v))
        .attr("x2", innerW).attr("y2", y(v))
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", -8).attr("y", y(v))
        .attr("text-anchor", "end")
        .attr("dominant-baseline", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(v);
    }

    // Linear reference line (1:1)
    g.append("line")
      .attr("x1", x(0)).attr("y1", y(0))
      .attr("x2", x(100)).attr("y2", y(100))
      .attr("stroke", "rgba(255,255,255,0.15)")
      .attr("stroke-width", 1)
      .attr("stroke-dasharray", "4,4");

    g.append("text")
      .attr("x", x(75))
      .attr("y", y(80))
      .attr("fill", "rgba(255,255,255,0.2)")
      .attr("font-size", 9)
      .attr("transform", `rotate(-35, ${x(75)}, ${y(80)})`)
      .text("Lineal (1:1)");

    // Compression curve
    const sorted = [...curves].sort((a, b) => a.inputDb - b.inputDb);

    const line = d3
      .line<{ inputDb: number; outputDb: number }>()
      .x((d) => x(d.inputDb))
      .y((d) => y(d.outputDb))
      .curve(d3.curveMonotoneX);

    g.append("path")
      .datum(sorted)
      .attr("d", line)
      .attr("fill", "none")
      .attr("stroke", "#f59e0b")
      .attr("stroke-width", 2);

    // Knee point marker
    const kneeData = sorted.find((d) => d.inputDb >= kneePoint);
    if (kneeData) {
      g.append("circle")
        .attr("cx", x(kneeData.inputDb))
        .attr("cy", y(kneeData.outputDb))
        .attr("r", 5)
        .attr("fill", "none")
        .attr("stroke", "#f59e0b")
        .attr("stroke-width", 2);

      // Vertical dashed line from knee
      g.append("line")
        .attr("x1", x(kneePoint)).attr("y1", y(kneeData.outputDb))
        .attr("x2", x(kneePoint)).attr("y2", innerH)
        .attr("stroke", "rgba(245,158,11,0.3)")
        .attr("stroke-dasharray", "3,3");

      g.append("text")
        .attr("x", x(kneePoint))
        .attr("y", y(kneeData.outputDb) - 12)
        .attr("text-anchor", "middle")
        .attr("fill", "#f59e0b")
        .attr("font-size", 9)
        .text(`Codo: ${kneePoint} dB`);
    }

    // Ratio display
    g.append("text")
      .attr("x", innerW)
      .attr("y", -5)
      .attr("text-anchor", "end")
      .attr("fill", "rgba(255,255,255,0.4)")
      .attr("font-size", 10)
      .text(`Ratio: ${ratio}`);

    // Axis labels
    g.append("text")
      .attr("x", innerW / 2).attr("y", innerH + 35)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Entrada (dB)");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerH / 2).attr("y", -38)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Salida (dB)");

    // Title
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text("Curva de Compresión");

  }, [curves, kneePoint, ratio, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
