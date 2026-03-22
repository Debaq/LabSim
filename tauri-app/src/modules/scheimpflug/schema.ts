import { z } from "zod/v4";

/**
 * Schema de datos fisiológicos del segmento anterior para tomografía Scheimpflug.
 *
 * A diferencia del topógrafo de Placido (solo superficie anterior),
 * el Scheimpflug captura toda la cámara anterior:
 * - Córnea anterior y posterior
 * - Cámara anterior (profundidad, ángulo)
 * - Cristalino (densidad, opacidad)
 */

export const CORNEAL_PATHOLOGIES = [
  "normal",
  "keratoconus",
  "pellucid",
  "post-lasik",
  "post-prk",
  "fuchs-dystrophy",
  "corneal-edema",
  "scarring",
] as const;

export const LENS_STATUS = [
  "clear",
  "cataract-nuclear",
  "cataract-cortical",
  "cataract-subcapsular",
  "pseudophakic",         // IOL (lente intraocular)
  "aphakic",              // sin cristalino
] as const;

export const SEVERITIES = ["leve", "moderado", "severo"] as const;

const eyeConfig = z.object({
  // ─── Córnea ────────────────────────────────────
  cornealPathology: z.enum(CORNEAL_PATHOLOGIES).default("normal"),
  severidad: z.enum(SEVERITIES).default("moderado"),

  /** K1 plano anterior (D). Normal: 42-44 */
  k1Anterior: z.coerce.number().min(30).max(65).optional(),
  /** K2 empinado anterior (D). Normal: 43-45 */
  k2Anterior: z.coerce.number().min(30).max(65).optional(),
  /** K1 posterior (D). Normal: -6.0 a -6.8 */
  k1Posterior: z.coerce.number().min(-10).max(0).optional(),
  /** K2 posterior (D). Normal: -6.2 a -7.0 */
  k2Posterior: z.coerce.number().min(-10).max(0).optional(),
  /** Eje K1 (grados) */
  kAxis: z.coerce.number().min(0).max(180).optional(),
  /** CCT central (µm). Normal: 520-560 */
  cct: z.coerce.number().min(300).max(800).optional(),
  /** Punto más delgado (µm) */
  thinnestPoint: z.coerce.number().min(250).max(800).optional(),

  // ─── Cámara anterior ───────────────────────────
  /** Profundidad cámara anterior (mm). Normal: 2.5-4.0 */
  acd: z.coerce.number().min(1).max(6).optional(),
  /** Ángulo iridocorneal (grados). Normal: 25-45. Estrecho: <20 */
  iridocornealAngle: z.coerce.number().min(0).max(60).optional(),
  /** Volumen cámara anterior (mm³). Normal: 120-200 */
  acVolume: z.coerce.number().min(50).max(300).optional(),

  // ─── Cristalino ────────────────────────────────
  lensStatus: z.enum(LENS_STATUS).default("clear"),
  /** Densitometría del cristalino (%). Normal <20%, catarata >30% */
  lensDensity: z.coerce.number().min(0).max(100).optional(),
  /** Espesor del cristalino (mm). Normal: 3.5-5.0 */
  lensThickness: z.coerce.number().min(2).max(7).optional(),

  notas: z.string().optional(),
});

export const scheimpflugSchema = z.object({
  ojoDerecho: eyeConfig.optional(),
  ojoIzquierdo: eyeConfig.optional(),
  observaciones: z.string().optional(),
});

export type ScheimpflugData = z.infer<typeof scheimpflugSchema>;
export type ScheimpflugEyeConfig = z.infer<typeof eyeConfig>;
