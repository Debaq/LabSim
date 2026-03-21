import { WaveformChart } from "./waveform-chart";
import type { WaveData } from "./waveform-chart";

export interface ABR80ChartProps {
  waves: WaveData[];
  ear: "right" | "left";
  width?: number;
  height?: number;
}

export function ABR80Chart({ waves, ear, width, height }: ABR80ChartProps) {
  return (
    <WaveformChart
      waves={waves}
      ear={ear}
      intensity="80dB"
      width={width}
      height={height}
    />
  );
}
