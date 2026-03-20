import { useRef, useEffect } from "react";
import * as d3 from "d3";

export interface TimpanogramData {
  ear: "right" | "left";
  type: "A" | "As" | "Ad" | "B" | "C";
  peakPressure: number;   // daPa
  peakCompliance: number; // ml
  volume: number;         // ml
}

interface TimpanogramChartProps {
  data: TimpanogramData[];
  width?: number;
  height?: number;
}

const MARGIN = { top: 25, right: 20, bottom: 40, left: 50 };

// Generate timpanogram curve from type
function generateCurve(
  data: TimpanogramData,
): { pressure: number; compliance: number }[] {
  const points: { pressure: number; compliance: number }[] = [];
  const { type, peakPressure, peakCompliance } = data;

  for (let p = -400; p <= 200; p += 5) {
    let compliance: number;

    switch (type) {
      case "A": {
        const sigma = 60;
        compliance =
          peakCompliance *
          Math.exp(-Math.pow(p - peakPressure, 2) / (2 * sigma * sigma));
        break;
      }
      case "As": {
        const sigma = 50;
        compliance =
          peakCompliance *
          Math.exp(-Math.pow(p - peakPressure, 2) / (2 * sigma * sigma));
        break;
      }
      case "Ad": {
        const sigma = 40;
        compliance =
          peakCompliance *
          Math.exp(-Math.pow(p - peakPressure, 2) / (2 * sigma * sigma));
        break;
      }
      case "B":
        compliance = 0.1 + Math.random() * 0.05;
        break;
      case "C": {
        const sigma = 55;
        compliance =
          peakCompliance *
          Math.exp(-Math.pow(p - peakPressure, 2) / (2 * sigma * sigma));
        break;
      }
    }

    points.push({ pressure: p, compliance: Math.max(0, compliance) });
  }

  return points;
}

export function TimpanogramChart({
  data,
  width = 500,
  height = 350,
}: TimpanogramChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const x = d3.scaleLinear().domain([-400, 200]).range([0, innerW]);
    const y = d3.scaleLinear().domain([0, 2.5]).range([innerH, 0]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${MARGIN.left},${MARGIN.top})`);

    // Normal zone shading
    g.append("rect")
      .attr("x", x(-100)).attr("y", 0)
      .attr("width", x(50) - x(-100)).attr("height", innerH)
      .attr("fill", "rgba(34, 197, 94, 0.04)");

    // Grid
    for (let p = -400; p <= 200; p += 100) {
      g.append("line")
        .attr("x1", x(p)).attr("y1", 0)
        .attr("x2", x(p)).attr("y2", innerH)
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", x(p)).attr("y", innerH + 18)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(p);
    }

    for (let c = 0; c <= 2.5; c += 0.5) {
      g.append("line")
        .attr("x1", 0).attr("y1", y(c))
        .attr("x2", innerW).attr("y2", y(c))
        .attr("stroke", "rgba(255,255,255,0.05)");
      g.append("text")
        .attr("x", -8).attr("y", y(c))
        .attr("text-anchor", "end")
        .attr("dominant-baseline", "middle")
        .attr("fill", "rgba(255,255,255,0.4)")
        .attr("font-size", 10)
        .text(c.toFixed(1));
    }

    // Axis labels
    g.append("text")
      .attr("x", innerW / 2).attr("y", innerH + 35)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Presión (daPa)");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerH / 2).attr("y", -38)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.3)")
      .attr("font-size", 11)
      .text("Compliance (ml)");

    // Draw curves
    data.forEach((d) => {
      const curveData = generateCurve(d);
      const color = d.ear === "right" ? "#ef4444" : "#3b82f6";

      const line = d3
        .line<{ pressure: number; compliance: number }>()
        .x((p) => x(p.pressure))
        .y((p) => y(p.compliance))
        .curve(d3.curveBasis);

      g.append("path")
        .datum(curveData)
        .attr("d", line)
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 2);

      // Peak marker
      if (d.type !== "B") {
        g.append("circle")
          .attr("cx", x(d.peakPressure))
          .attr("cy", y(d.peakCompliance))
          .attr("r", 4)
          .attr("fill", color)
          .attr("fill-opacity", 0.8);

        // Label
        g.append("text")
          .attr("x", x(d.peakPressure))
          .attr("y", y(d.peakCompliance) - 12)
          .attr("text-anchor", "middle")
          .attr("fill", color)
          .attr("font-size", 9)
          .text(`${d.type} (${d.peakPressure} daPa)`);
      }
    });

    // Title
    svg
      .append("text")
      .attr("x", width / 2).attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("font-size", 12)
      .attr("font-weight", "bold")
      .text("Timpanograma");

  }, [data, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="select-none" />;
}
