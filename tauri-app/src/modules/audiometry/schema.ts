import { z } from "zod/v4";

const thresholdObj = z.record(z.string(), z.coerce.number().min(-10).max(130).nullable().optional());

export const audiometrySchema = z.object({
  umbralesAereos: z.object({
    oidoDerecho: thresholdObj.default({}),
    oidoIzquierdo: thresholdObj.default({}),
  }),
  umbralesOseos: z.object({
    oidoDerecho: thresholdObj.default({}),
    oidoIzquierdo: thresholdObj.default({}),
  }),
  ldl: z.object({
    oidoDerecho: thresholdObj.default({}),
    oidoIzquierdo: thresholdObj.default({}),
  }),
  observaciones: z.string().optional(),
});

export type AudiometryData = z.infer<typeof audiometrySchema>;
