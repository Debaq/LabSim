/**
 * Validación de coherencia entre datos audiológicos.
 *
 * Verifica que los datos del paciente son audiológicamente consistentes.
 * Se usa en el editor del paciente para mostrar advertencias al docente.
 */

import type { AudiometryData, HearingLossType } from "@/modules/audiometry/schema";
import type { LogoaudiometryData } from "@/modules/logoaudiometry/schema";
import type { SupraliminalData } from "@/modules/supraliminal/schema";
import type { TuningForkData } from "@/modules/tuning-fork/schema";
import { calculatePTA } from "@/lib/audiometry-patient";

export interface CoherenceWarning {
  severity: "error" | "warning";
  module: string;
  message: string;
}

type EarKey = "oidoDerecho" | "oidoIzquierdo";
const EARS: { key: EarKey; label: string }[] = [
  { key: "oidoDerecho", label: "OD" },
  { key: "oidoIzquierdo", label: "OI" },
];

function getVal(record: Record<string, number | null | undefined> | undefined, freq: string): number | null {
  const v = record?.[freq];
  return v != null ? Number(v) : null;
}

export function validateCoherence(
  audiometry: AudiometryData | undefined,
  logoaudiometry?: LogoaudiometryData,
  supraliminal?: SupraliminalData,
  tuningFork?: TuningForkData,
): CoherenceWarning[] {
  if (!audiometry) return [];
  const warnings: CoherenceWarning[] = [];

  for (const { key, label } of EARS) {
    const air = audiometry.umbralesAereos?.[key] ?? {};
    const bone = audiometry.umbralesOseos?.[key] ?? {};
    const type: HearingLossType = audiometry.tipoPerdida?.[key] ?? "normal";

    // ─── VO ≤ VA en cada frecuencia (error) ───────────
    for (const freq of Object.keys(bone)) {
      const boneVal = getVal(bone, freq);
      const airVal = getVal(air, freq);
      if (boneVal != null && airVal != null && boneVal > airVal) {
        warnings.push({
          severity: "error",
          module: "Audiometría",
          message: `${label}: VO (${boneVal} dB) > VA (${airVal} dB) a ${freq} Hz. La vía ósea no puede ser peor que la aérea.`,
        });
      }
    }

    // ─── Tipo de pérdida vs GAP ───────────────────────
    const hasGap = Object.keys(air).some((f) => {
      const a = getVal(air, f);
      const b = getVal(bone, f);
      return a != null && b != null && (a - b) >= 15;
    });

    if (type === "normal" && hasGap) {
      warnings.push({
        severity: "warning",
        module: "Audiometría",
        message: `${label}: Tipo "Normal" pero hay GAP aéreo-óseo ≥ 15 dB. Considerar tipo conductiva o mixta.`,
      });
    }

    if ((type === "sensorioneural-coclear" || type === "sensorioneural-retrococlear") && hasGap) {
      warnings.push({
        severity: "warning",
        module: "Audiometría",
        message: `${label}: Tipo "Sensorioneural" pero hay GAP significativo. Considerar tipo mixta.`,
      });
    }

    if (type === "conductiva" && !hasGap && Object.keys(air).length > 0 && Object.keys(bone).length > 0) {
      warnings.push({
        severity: "warning",
        module: "Audiometría",
        message: `${label}: Tipo "Conductiva" pero no hay GAP aéreo-óseo significativo.`,
      });
    }
  }

  // ─── SRT vs PTA ─────────────────────────────────────
  if (logoaudiometry) {
    for (const { key, label } of EARS) {
      const earSide = key === "oidoDerecho" ? "right" as const : "left" as const;
      const ptaVal = calculatePTA(audiometry, earSide);
      const srt = logoaudiometry.srt?.[key];

      if (ptaVal != null && srt != null) {
        const diff = Math.abs(srt - ptaVal);
        if (diff > 10) {
          warnings.push({
            severity: "warning",
            module: "Logoaudiometría",
            message: `${label}: SRT (${srt} dB) difiere del PTA (${ptaVal} dB) en ${diff} dB. Diferencia esperada ≤ 10 dB.`,
          });
        }
      }
    }
  }

  // ─── SISI coherente con tipo ────────────────────────
  if (supraliminal) {
    for (const { key, label } of EARS) {
      const type: HearingLossType = audiometry.tipoPerdida?.[key] ?? "normal";
      const earKey = key === "oidoDerecho" ? "od" : "oi";
      const sisiVals = Object.values(supraliminal.sisi?.[earKey] ?? {}).filter((v): v is number => v != null);

      if (sisiVals.length > 0) {
        const avgSisi = sisiVals.reduce((a, b) => a + b, 0) / sisiVals.length;

        if (type === "sensorioneural-coclear" && avgSisi < 40) {
          warnings.push({
            severity: "warning",
            module: "Supraliminal",
            message: `${label}: SISI promedio ${Math.round(avgSisi)}% es bajo para lesión coclear. Esperado ≥ 70%.`,
          });
        }
        if ((type === "normal" || type === "conductiva") && avgSisi > 50) {
          warnings.push({
            severity: "warning",
            module: "Supraliminal",
            message: `${label}: SISI promedio ${Math.round(avgSisi)}% es alto para tipo "${type}". Esperado < 20%.`,
          });
        }
      }

      // Carhart coherente
      const carhartVals = Object.values(supraliminal.carhart?.[earKey] ?? {}).filter((v): v is number => v != null);
      if (carhartVals.length > 0) {
        const avgCarhart = carhartVals.reduce((a, b) => a + b, 0) / carhartVals.length;

        if (type === "sensorioneural-retrococlear" && avgCarhart < 10) {
          warnings.push({
            severity: "warning",
            module: "Supraliminal",
            message: `${label}: Tone Decay promedio ${Math.round(avgCarhart)} dB es bajo para lesión retrococlear. Esperado ≥ 15 dB.`,
          });
        }
        if ((type === "normal" || type === "conductiva") && avgCarhart > 10) {
          warnings.push({
            severity: "warning",
            module: "Supraliminal",
            message: `${label}: Tone Decay promedio ${Math.round(avgCarhart)} dB es alto para tipo "${type}". Esperado < 5 dB.`,
          });
        }
      }
    }
  }

  // ─── Diapasones coherentes ──────────────────────────
  if (tuningFork) {
    for (const { key, label } of EARS) {
      const type: HearingLossType = audiometry.tipoPerdida?.[key] ?? "normal";
      const rinne = tuningFork.rinne?.[key];
      const schwabach = tuningFork.schwabach?.[key];

      // Rinne
      if (rinne) {
        if ((type === "conductiva" || type === "mixta") && rinne === "positivo") {
          const air = getVal(audiometry.umbralesAereos?.[key] ?? {}, "500");
          const bone = getVal(audiometry.umbralesOseos?.[key] ?? {}, "500");
          if (air != null && bone != null && (air - bone) >= 15) {
            warnings.push({
              severity: "warning",
              module: "Acumetría",
              message: `${label}: Rinne positivo con GAP ≥ 15 dB. Se espera Rinne negativo en pérdida conductiva.`,
            });
          }
        }
        if ((type === "normal" || type === "sensorioneural-coclear" || type === "sensorioneural-retrococlear") && rinne === "negativo") {
          warnings.push({
            severity: "warning",
            module: "Acumetría",
            message: `${label}: Rinne negativo con tipo "${type}". Se espera Rinne positivo.`,
          });
        }
      }

      // Schwabach
      if (schwabach) {
        if ((type === "sensorioneural-coclear" || type === "sensorioneural-retrococlear") && schwabach === "alargado") {
          warnings.push({
            severity: "warning",
            module: "Acumetría",
            message: `${label}: Schwabach alargado con lesión sensorioneural. Se espera acortado.`,
          });
        }
        if (type === "conductiva" && schwabach === "acortado") {
          warnings.push({
            severity: "warning",
            module: "Acumetría",
            message: `${label}: Schwabach acortado con pérdida conductiva. Se espera alargado.`,
          });
        }
      }
    }

    // Weber
    if (tuningFork.weber?.lateralizacion) {
      const lat = tuningFork.weber.lateralizacion;
      const rightType = audiometry.tipoPerdida?.oidoDerecho ?? "normal";
      const leftType = audiometry.tipoPerdida?.oidoIzquierdo ?? "normal";

      // Conductiva unilateral derecha debe lateralizar a derecha
      if (rightType === "conductiva" && leftType === "normal" && lat === "izquierda") {
        warnings.push({
          severity: "warning",
          module: "Acumetría",
          message: "Weber lateraliza a izquierda, pero la pérdida conductiva es derecha. Se espera lateralización al oído enfermo.",
        });
      }
      if (leftType === "conductiva" && rightType === "normal" && lat === "derecha") {
        warnings.push({
          severity: "warning",
          module: "Acumetría",
          message: "Weber lateraliza a derecha, pero la pérdida conductiva es izquierda. Se espera lateralización al oído enfermo.",
        });
      }
    }
  }

  return warnings;
}
