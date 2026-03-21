import { z } from "zod/v4";

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
  defecto: z.enum(DEFECT_TYPES).default("normal"),
  severidad: z.enum(SEVERITIES).default("moderado"),
  patron: z.enum(["24-2", "30-2", "10-2"]).default("24-2"),
  estrategia: z.enum(["sita-standard", "sita-fast", "full-threshold"]).default("sita-standard"),
  tamanoEstimulo: z.enum(["I", "II", "III", "IV", "V"]).default("III"),
  mdObjetivo: z.coerce.number().nullable().optional(),
  confiabilidadBuena: z.boolean().default(true),
  notas: z.string().optional(),
});

export const visualFieldSchema = z.object({
  ojoDerecho: eyeConfig,
  ojoIzquierdo: eyeConfig,
  observaciones: z.string().optional(),
});

export type VisualFieldData = z.infer<typeof visualFieldSchema>;
export type VFEyeConfig = z.infer<typeof eyeConfig>;
