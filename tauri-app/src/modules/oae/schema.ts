import { z } from "zod/v4";

const oaePoint = z.object({
  frequency: z.coerce.number(),
  amplitude: z.coerce.number(),
  noiseFloor: z.coerce.number(),
  snr: z.coerce.number(),
  pass: z.boolean(),
});

export const oaeSchema = z.object({
  teoae: z.object({
    oidoDerecho: z.object({
      reproducibilidad: z.coerce.number().nullable().optional(),
      resultado: z.string().optional(),
      datos: z.array(oaePoint).default([]),
    }),
    oidoIzquierdo: z.object({
      reproducibilidad: z.coerce.number().nullable().optional(),
      resultado: z.string().optional(),
      datos: z.array(oaePoint).default([]),
    }),
  }),
  dpoae: z.object({
    oidoDerecho: z.object({
      resultado: z.string().optional(),
      datos: z.array(oaePoint).default([]),
    }),
    oidoIzquierdo: z.object({
      resultado: z.string().optional(),
      datos: z.array(oaePoint).default([]),
    }),
  }),
  observaciones: z.string().optional(),
});

export type OaeData = z.infer<typeof oaeSchema>;
