import { z } from "zod/v4";

export const RINNE_RESULTS = ["positivo", "negativo", "indefinido"] as const;
export const WEBER_RESULTS = ["derecha", "izquierda", "central", "no-lateraliza"] as const;
export const SCHWABACH_RESULTS = ["normal", "acortado", "alargado"] as const;

export const tuningForkSchema = z.object({
  rinne: z.object({
    oidoDerecho: z.enum(RINNE_RESULTS).nullable().optional(),
    oidoIzquierdo: z.enum(RINNE_RESULTS).nullable().optional(),
  }).default({ oidoDerecho: null, oidoIzquierdo: null }),
  weber: z.object({
    lateralizacion: z.enum(WEBER_RESULTS).nullable().optional(),
  }).default({ lateralizacion: null }),
  schwabach: z.object({
    oidoDerecho: z.enum(SCHWABACH_RESULTS).nullable().optional(),
    oidoIzquierdo: z.enum(SCHWABACH_RESULTS).nullable().optional(),
  }).default({ oidoDerecho: null, oidoIzquierdo: null }),
  observaciones: z.string().optional(),
});

export type TuningForkData = z.infer<typeof tuningForkSchema>;
