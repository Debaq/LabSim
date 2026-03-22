import { z } from "zod/v4";

/**
 * Schema de datos fisiológicos del ojo para campimetría.
 *
 * El docente define:
 * - Tipo de defecto y severidad (generan sensibilidades por punto)
 * - Comportamiento del paciente durante el examen (cooperación, fatiga, fijación)
 * - Parámetros de protocolo predefinidos (opcional)
 *
 * El equipo NO interpreta — presenta estímulos y el paciente simulado responde.
 */

export const DEFECT_TYPES = [
  "normal",
  "escotoma-arcuato-sup",
  "escotoma-arcuato-inf",
  "escotoma-arcuato-doble",
  "escalon-nasal",
  "hemianopsia-homonima-der",
  "hemianopsia-homonima-izq",
  "hemianopsia-bitemporal",
  "cuadrantanopsia-sup",
  "cuadrantanopsia-inf",
  "depresion-general",
  "isla-central",
  "constriccion-periferica",
] as const;

export const SEVERITIES = ["leve", "moderado", "severo"] as const;

const eyeConfig = z.object({
  // ─── Defecto visual ────────────────────────────
  defecto: z.enum(DEFECT_TYPES).default("normal"),
  severidad: z.enum(SEVERITIES).default("moderado"),
  /** MD objetivo (dB) para ajustar profundidad del defecto */
  mdObjetivo: z.coerce.number().nullable().optional(),

  // ─── Comportamiento del paciente en el examen ──
  /** Tasa de falsos positivos (0-1). Paciente aprieta sin estímulo */
  falsePositiveRate: z.coerce.number().min(0).max(1).optional(),
  /** Tasa de falsos negativos (0-1). No responde aunque vea */
  falseNegativeRate: z.coerce.number().min(0).max(1).optional(),
  /** Tasa de pérdida de fijación (0-1). Se mueve del punto de fijación */
  fixationLossRate: z.coerce.number().min(0).max(1).optional(),
  /** Variabilidad en tiempo de reacción (ms). Normal ~200-400ms */
  reactionTimeMs: z.coerce.number().min(100).max(2000).optional(),
  /** Factor de fatiga (0-1). Qué tanto empeora al avanzar el test */
  fatigueFactor: z.coerce.number().min(0).max(1).optional(),

  // ─── Protocolo preferido (opcional) ────────────
  patron: z.enum(["24-2", "30-2", "10-2"]).optional(),
  estrategia: z.enum(["sita-standard", "sita-fast", "full-threshold"]).optional(),
  tamanoEstimulo: z.enum(["I", "II", "III", "IV", "V"]).optional(),

  notas: z.string().optional(),
});

export const visualFieldSchema = z.object({
  ojoDerecho: eyeConfig.optional(),
  ojoIzquierdo: eyeConfig.optional(),
  observaciones: z.string().optional(),
});

export type VisualFieldData = z.infer<typeof visualFieldSchema>;
export type VFEyeConfig = z.infer<typeof eyeConfig>;
