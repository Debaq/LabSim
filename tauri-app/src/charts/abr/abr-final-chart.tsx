import { WaveformChart } from "./waveform-chart";
import type { WaveData } from "./waveform-chart";

export interface ABRFinalChartProps {
  waves: WaveData[];
  ear: "right" | "left";
  width?: number;
  height?: number;
}

export function ABRFinalChart({ waves, ear, width, height }: ABRFinalChartProps) {
  return (
    <WaveformChart
      waves={waves}
      ear={ear}
      intensity="final"
      width={width}
      height={height}
    />
  );
}
