import { z } from "zod/v4";

/**
 * Schema de datos fisiológicos del ojo para OCT.
 *
 * El docente define patología, severidad, parámetros reales de espesores,
 * y comportamiento del paciente durante la captura.
 */

export const PATHOLOGIES = [
  "normal", "glaucoma", "edema", "drusen", "epiretinal", "amd-dry", "amd-wet",
] as const;

export const SEVERITIES = ["leve", "moderado", "severo"] as const;

const eyeConfig = z.object({
  // ─── Patología y severidad ─────────────────────
  patologia: z.enum(PATHOLOGIES).default("normal"),
  severidad: z.enum(SEVERITIES).default("moderado"),
  scanPreferido: z.enum(["disco", "macula"]).default("disco"),

  // ─── Parámetros fisiológicos (opcional) ────────
  /** RNFL promedio global (µm). Normal: 90-120 */
  rnflAvg: z.coerce.number().min(20).max(200).optional(),
  /** GCL+IPL promedio (µm). Normal: 75-95 */
  gclIplAvg: z.coerce.number().min(20).max(150).optional(),
  /** Espesor macular central (µm). Normal: 270-310 */
  centralMacularThickness: z.coerce.number().min(100).max(800).optional(),

  notas: z.string().optional(),
});

export const octSchema = z.object({
  ojoDerecho: eyeConfig.optional(),
  ojoIzquierdo: eyeConfig.optional(),
  observaciones: z.string().optional(),
});

export type OctData = z.infer<typeof octSchema>;
export type OctEyeConfig = z.infer<typeof eyeConfig>;
