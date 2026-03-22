/**
 * Panel de índices de cámara anterior.
 * Muestra queratometría anterior/posterior, paquimetría, ACD, volumen, ángulo, densitometría.
 */

import type { AnteriorChamberIndices } from "@/lib/scheimpflug-synthetic";

interface Props {
  indices: AnteriorChamberIndices;
}

export function ACIndicesPanel({ indices }: Props) {
  return (
    <div className="space-y-2 p-2 text-[10px]">
      {/* Queratometría anterior */}
      <Section title="K Anterior">
        <Row label="K1 (flat)" value={`${indices.k1Ant} D`} />
        <Row label="K2 (steep)" value={`${indices.k2Ant} D`} />
        <Row label="K avg" value={`${indices.kAvgAnt} D`} />
        <Row label="Eje" value={`${indices.kAxisAnt}°`} />
        <Row label="Cyl" value={`${(indices.k2Ant - indices.k1Ant).toFixed(2)} D`} />
      </Section>

      {/* Queratometría posterior */}
      <Section title="K Posterior">
        <Row label="K1" value={`${indices.k1Post} D`} />
        <Row label="K2" value={`${indices.k2Post} D`} />
      </Section>

      {/* Paquimetría */}
      <Section title="Paquimetría">
        <Row label="CCT" value={`${indices.cct} µm`} warn={indices.cct < 500} />
        <Row label="Thinnest" value={`${indices.thinnest} µm`} warn={indices.thinnest < 470} />
        <Row label="Ubicación" value={`(${indices.thinnestX}, ${indices.thinnestY}) mm`} />
      </Section>

      {/* Cámara anterior */}
      <Section title="Cámara Anterior">
        <Row label="ACD" value={`${indices.acd} mm`} warn={indices.acd < 2.5} />
        <Row label="Volumen" value={`${indices.acVolume} mm³`} />
        <Row label="Ángulo" value={`${indices.iridocornealAngle}°`} warn={indices.iridocornealAngle < 20} />
      </Section>

      {/* Cristalino */}
      <Section title="Cristalino">
        <Row label="Densidad" value={`${indices.lensDensity}%`} warn={indices.lensDensity > 30} />
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <span className="text-[8px] ls-text-muted uppercase tracking-wider">{title}</span>
      <div className="mt-0.5 space-y-0.5">{children}</div>
    </div>
  );
}

function Row({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className="ls-text-muted">{label}</span>
      <span className={`font-mono ${warn ? "text-red-400" : "ls-text2"}`}>{value}</span>
    </div>
  );
}
