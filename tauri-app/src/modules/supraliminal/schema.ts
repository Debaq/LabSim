import { z } from "zod/v4";

const freqValues = z.record(z.string(), z.coerce.number().nullable().optional());

export const supraliminalSchema = z.object({
  sisi: z.object({
    od: freqValues.default({}),
    oi: freqValues.default({}),
  }),
  carhart: z.object({
    od: freqValues.default({}),
    oi: freqValues.default({}),
  }),
  maspetiol: z.object({
    od: z.string().nullable().optional(),
    oi: z.string().nullable().optional(),
  }),
  fowler: z.record(
    z.string(),
    z.object({
      resultado: z.string().nullable().optional(),
      diferencia: z.coerce.number().nullable().optional(),
    }),
  ).default({}),
  luscher: z.object({
    od: freqValues.default({}),
    oi: freqValues.default({}),
  }),
  observaciones: z.string().optional(),
});

export type SupraliminalData = z.infer<typeof supraliminalSchema>;
