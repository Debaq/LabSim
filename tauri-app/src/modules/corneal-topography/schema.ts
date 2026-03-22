import { z } from "zod/v4";

/**
 * Schema de datos fisiológicos de la córnea para topografía.
 *
 * El docente define los parámetros reales de la córnea.
 * El generador produce mapas coherentes a partir de estos datos.
 * El equipo muestra los mapas — no interpreta.
 */

export const PATHOLOGIES = [
  "normal",
  "keratoconus",
  "pellucid",
  "wtr-astigmatism",
  "atr-astigmatism",
  "oblique-astigmatism",
  "post-lasik",
] as const;

export const SEVERITIES = ["leve", "moderado", "severo"] as const;

const eyeConfig = z.object({
  // ─── Tipo de córnea ────────────────────────────
  patologia: z.enum(PATHOLOGIES).default("normal"),
  severidad: z.enum(SEVERITIES).default("moderado"),

  // ─── Parámetros queratométricos reales ─────────
  /** K plano (D). Normal: 42-44 */
  k1: z.coerce.number().min(30).max(65).optional(),
  /** K empinado (D). Normal: 43-45 */
  k2: z.coerce.number().min(30).max(65).optional(),
  /** Eje del K plano (grados 0-180) */
  k1Axis: z.coerce.number().min(0).max(180).optional(),
  /** Espesor corneal central (µm). Normal: 520-560 */
  cct: z.coerce.number().min(300).max(700).optional(),
  /** Espesor mínimo (µm). Normal: ~510-550 */
  thinnestPoint: z.coerce.number().min(250).max(700).optional(),

  notas: z.string().optional(),
});

export const cornealTopographySchema = z.object({
  ojoDerecho: eyeConfig.optional(),
  ojoIzquierdo: eyeConfig.optional(),
  observaciones: z.string().optional(),
});

export type CornealTopographyData = z.infer<typeof cornealTopographySchema>;
export type CornealTopographyEyeConfig = z.infer<typeof eyeConfig>;
