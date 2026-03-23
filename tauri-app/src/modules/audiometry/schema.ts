import { z } from "zod/v4";

const thresholdObj = z.record(z.string(), z.coerce.number().min(-10).max(130).nullable().optional());

// ─── Tipos de pérdida auditiva ──────────────────────
export const HEARING_LOSS_TYPES = [
  "normal",
  "conductiva",
  "sensorioneural-coclear",
  "sensorioneural-retrococlear",
  "mixta",
] as const;
export type HearingLossType = (typeof HEARING_LOSS_TYPES)[number];

const hearingLossEnum = z.enum(HEARING_LOSS_TYPES).default("normal");

// ─── Configuración del paciente audiométrico ────────
const earClassification = z.object({
  oidoDerecho: hearingLossEnum,
  oidoIzquierdo: hearingLossEnum,
});

const earBooleans = z.object({
  oidoDerecho: z.boolean().default(false),
  oidoIzquierdo: z.boolean().default(false),
});

export const patientAudioConfigSchema = z.object({
  falsePositiveRate: z.coerce.number().min(0).max(0.3).default(0.03),
  falseNegativeRate: z.coerce.number().min(0).max(0.3).default(0.02),
  reactionTimeMs: z.coerce.number().min(100).max(2000).default(350),
  fatigueFactor: z.coerce.number().min(0).max(1).default(0.1),
  seed: z.coerce.number().default(42),
});

// ─── Schema principal ───────────────────────────────
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
  // ─── Perfil audiológico (clasifica la patología) ──
  tipoPerdida: earClassification.default({
    oidoDerecho: "normal",
    oidoIzquierdo: "normal",
  }),
  reclutamiento: earBooleans.default({
    oidoDerecho: false,
    oidoIzquierdo: false,
  }),
  deterioroTonal: earBooleans.default({
    oidoDerecho: false,
    oidoIzquierdo: false,
  }),
  // ─── Config del paciente virtual ──────────────────
  patientConfig: patientAudioConfigSchema.default({
    falsePositiveRate: 0.03,
    falseNegativeRate: 0.02,
    reactionTimeMs: 350,
    fatigueFactor: 0.1,
    seed: 42,
  }),
  observaciones: z.string().optional(),
});

export type AudiometryData = z.infer<typeof audiometrySchema>;
export type PatientAudioConfig = z.infer<typeof patientAudioConfigSchema>;
