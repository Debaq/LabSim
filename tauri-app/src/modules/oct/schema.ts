import { z } from "zod/v4";

export const PATHOLOGIES = [
  "normal", "glaucoma", "edema", "drusen", "epiretinal", "amd-dry", "amd-wet",
] as const;

export const SEVERITIES = ["leve", "moderado", "severo"] as const;

const eyeConfig = z.object({
  patologia: z.enum(PATHOLOGIES).default("normal"),
  severidad: z.enum(SEVERITIES).default("moderado"),
  scanPreferido: z.enum(["disco", "macula"]).default("disco"),
  calidadSenal: z.coerce.number().min(1).max(10).default(8),
  notas: z.string().optional(),
});

export const octSchema = z.object({
  ojoDerecho: eyeConfig,
  ojoIzquierdo: eyeConfig,
  observaciones: z.string().optional(),
});

export type OctData = z.infer<typeof octSchema>;
export type OctEyeConfig = z.infer<typeof eyeConfig>;
