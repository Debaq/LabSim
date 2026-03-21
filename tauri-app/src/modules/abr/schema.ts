import { z } from "zod/v4";

const wave = z.object({
  presente: z.boolean().default(false),
  latencia: z.coerce.number().min(0).max(15).nullable().optional(),
  amplitud: z.coerce.number().min(0).max(5).nullable().optional(),
  replicabilidad: z.coerce.number().nullable().optional(),
});

const defaultWave = { presente: false } as const;

const defaultIntensitySet = {
  ondaI: defaultWave,
  ondaII: defaultWave,
  ondaIII: defaultWave,
  ondaIV: defaultWave,
  ondaV: defaultWave,
} as const;

const defaultEarData = {
  db80: defaultIntensitySet,
  final: defaultIntensitySet,
} as const;

const intensitySet = z.object({
  ondaI: wave.default(defaultWave),
  ondaII: wave.default(defaultWave),
  ondaIII: wave.default(defaultWave),
  ondaIV: wave.default(defaultWave),
  ondaV: wave.default(defaultWave),
});

const earData = z.object({
  db80: intensitySet.default(defaultIntensitySet),
  final: intensitySet.default(defaultIntensitySet),
});

export const abrSchema = z.object({
  stimulusActivo: z.string().default("click"),
  toneBurstActivo: z.string().default("1k"),
  click: z.object({
    oidoDerecho: earData.default(defaultEarData),
    oidoIzquierdo: earData.default(defaultEarData),
  }),
  toneBurst: z.record(z.string(), z.object({
    oidoDerecho: earData.default(defaultEarData),
    oidoIzquierdo: earData.default(defaultEarData),
  })).default({}),
  chirp: z.object({
    oidoDerecho: earData.default(defaultEarData),
    oidoIzquierdo: earData.default(defaultEarData),
  }),
  observaciones: z.string().optional(),
});

export type AbrData = z.infer<typeof abrSchema>;
