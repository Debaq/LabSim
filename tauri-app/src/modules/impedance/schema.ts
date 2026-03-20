import { z } from "zod/v4";

const timpData = z.object({
  complianceMaxima: z.coerce.number().min(0).max(10).nullable().optional(),
  presion: z.coerce.number().min(-400).max(200).nullable().optional(),
  volumenEac: z.coerce.number().min(0).max(10).nullable().optional(),
  gradiente: z.coerce.number().nullable().optional(),
});

const reflexRow = z.record(z.string(), z.string().default(""));

export const impedanceSchema = z.object({
  timpanometria: z.object({
    oidoDerecho: timpData.default({}),
    oidoIzquierdo: timpData.default({}),
  }),
  reflejosAcusticos: z.object({
    oidoDerecho: z.object({
      ipsi: reflexRow.default({}),
      contra: reflexRow.default({}),
    }),
    oidoIzquierdo: z.object({
      ipsi: reflexRow.default({}),
      contra: reflexRow.default({}),
    }),
  }),
  observaciones: z.string().optional(),
});

export type ImpedanceData = z.infer<typeof impedanceSchema>;
