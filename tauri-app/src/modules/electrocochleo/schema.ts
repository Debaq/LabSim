import { z } from "zod/v4";

export const electrocochleoSchema = z.object({
  sp: z.object({
    oidoDerecho: z.coerce.number().nullable().optional(),
    oidoIzquierdo: z.coerce.number().nullable().optional(),
  }),
  ap: z.object({
    oidoDerecho: z.coerce.number().nullable().optional(),
    oidoIzquierdo: z.coerce.number().nullable().optional(),
  }),
  params: z.object({
    fs: z.coerce.number().default(44100),
    windowMs: z.coerce.number().default(10),
    invert: z.boolean().default(false),
    smooth: z.coerce.number().default(0),
  }),
  observaciones: z.string().optional(),
});

export type ElectrocochleoData = z.infer<typeof electrocochleoSchema>;
