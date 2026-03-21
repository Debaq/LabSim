import { z } from "zod/v4";

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
  patologia: z.enum(PATHOLOGIES).default("normal"),
  severidad: z.enum(SEVERITIES).default("moderado"),
  mapaPreferido: z.enum(["axial", "tangential", "elevation", "pachymetry"]).default("axial"),
  calidadCaptura: z.coerce.number().min(1).max(10).default(8),
  notas: z.string().optional(),
});

export const cornealTopographySchema = z.object({
  ojoDerecho: eyeConfig,
  ojoIzquierdo: eyeConfig,
  observaciones: z.string().optional(),
});

export type CornealTopographyData = z.infer<typeof cornealTopographySchema>;
export type CornealTopographyEyeConfig = z.infer<typeof eyeConfig>;
