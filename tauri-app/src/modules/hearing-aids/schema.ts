import { z } from "zod/v4";

export const hearingAidsSchema = z.object({
  history: z.object({
    usoAnterior: z.boolean().default(false),
    marca: z.string().optional(),
    modelo: z.string().optional(),
    anosUso: z.coerce.number().nullable().optional(),
    tipoAnterior: z.string().optional(),
    satisfaccion: z.coerce.number().min(0).max(10).nullable().optional(),
    motivoCambio: z.string().optional(),
  }),
  prescripcion: z.object({
    formula: z.string().default("NAL-NL2"),
    tipoAudifono: z.string().optional(),
    moldeTipo: z.string().optional(),
    ventilacion: z.string().optional(),
    oidoDerecho: z.boolean().default(false),
    oidoIzquierdo: z.boolean().default(false),
  }),
  fieldAudio: z.object({
    sinAudifonos: z.record(z.string(), z.coerce.number().nullable().optional()).default({}),
    conAudifonos: z.record(z.string(), z.coerce.number().nullable().optional()).default({}),
    gananciaFuncional: z.record(z.string(), z.coerce.number().nullable().optional()).default({}),
  }),
  trial: z.object({
    marca: z.string().optional(),
    modelo: z.string().optional(),
    programa: z.string().optional(),
    logoConAudifonos: z.coerce.number().nullable().optional(),
    logoSinAudifonos: z.coerce.number().nullable().optional(),
    satisfaccion: z.coerce.number().min(0).max(10).nullable().optional(),
    observaciones: z.string().optional(),
  }),
  observaciones: z.string().optional(),
});

export type HearingAidsData = z.infer<typeof hearingAidsSchema>;
