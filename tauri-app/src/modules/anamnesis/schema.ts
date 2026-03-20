import { z } from "zod/v4";

export const anamnesisSchema = z.object({
  motivoConsulta: z.object({
    sintomaPrincipal: z.string().min(1, "Requerido"),
    severidad: z.string().optional(),
    tiempoEvolucion: z.string().optional(),
    descripcion: z.string().optional(),
  }),
  historiaLibre: z.object({
    cooperativo: z.boolean().default(true),
    orientado: z.boolean().default(true),
    confiable: z.boolean().default(true),
    acompanado: z.boolean().default(false),
    observaciones: z.string().optional(),
  }),
  antecedentesMorbidos: z.object({
    condiciones: z.array(z.string()).default([]),
  }),
  exposicionRuido: z.object({
    ocupacional: z.string().optional(),
    anosExposicion: z.coerce.number().min(0).max(80).optional(),
    proteccionAuditiva: z.string().optional(),
    recreacional: z.string().optional(),
  }),
  tinnitus: z.object({
    presencia: z.string().default("ausente"),
    lateralidad: z.string().optional(),
    tipo: z.string().optional(),
    severidad: z.coerce.number().min(0).max(10).default(0),
    constante: z.boolean().default(false),
    intermitente: z.boolean().default(false),
    empeoraNoche: z.boolean().default(false),
    afectaSueno: z.boolean().default(false),
    afectaConcentracion: z.boolean().default(false),
  }),
});

export type AnamnesisData = z.infer<typeof anamnesisSchema>;
