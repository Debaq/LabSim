import { z } from "zod/v4";

const umdEntry = z.object({
  intensidad: z.coerce.number().min(0).max(100).nullable().optional(),
  porcentaje: z.coerce.number().min(0).max(100).nullable().optional(),
}).default({ intensidad: null, porcentaje: null });

const umdSet = z.object({
  umd1: umdEntry,
  umd2: umdEntry,
  umd3: umdEntry,
}).default({
  umd1: { intensidad: null, porcentaje: null },
  umd2: { intensidad: null, porcentaje: null },
  umd3: { intensidad: null, porcentaje: null },
});

export const logoaudiometrySchema = z.object({
  sdt: z.object({
    oidoDerecho: z.coerce.number().min(0).max(100).nullable().optional(),
    oidoIzquierdo: z.coerce.number().min(0).max(100).nullable().optional(),
  }),
  srt: z.object({
    oidoDerecho: z.coerce.number().min(0).max(100).nullable().optional(),
    oidoIzquierdo: z.coerce.number().min(0).max(100).nullable().optional(),
  }),
  umd: z.object({
    oidoDerecho: umdSet,
    oidoIzquierdo: umdSet,
  }),
  observaciones: z.string().optional(),
});

export type LogoaudiometryData = z.infer<typeof logoaudiometrySchema>;
