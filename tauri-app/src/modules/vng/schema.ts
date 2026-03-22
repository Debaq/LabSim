import { z } from "zod/v4";

/**
 * Schema de datos fisiológicos vestibulares para VNG.
 *
 * El VNG es una estación de trabajo modular. El operador elige qué prueba hacer.
 * Cada prueba tiene sus propios datos fisiológicos del paciente.
 * Si el docente no configura una prueba, da resultado normal.
 */

// ─── Nistagmo espontáneo ─────────────────────────────

const spontaneousSchema = z.object({
  direction: z.enum(["derecha", "izquierda", "ninguno"]).optional(),
  spv: z.coerce.number().min(0).max(50).optional(),
  fixationSuppression: z.boolean().optional(),
});

// ─── Prueba calórica ─────────────────────────────────

const caloricSchema = z.object({
  rightWarmSpv: z.coerce.number().min(0).max(80).optional(),
  rightCoolSpv: z.coerce.number().min(0).max(80).optional(),
  leftWarmSpv: z.coerce.number().min(0).max(80).optional(),
  leftCoolSpv: z.coerce.number().min(0).max(80).optional(),
});

// ─── Posicionales ────────────────────────────────────

const positionalNystagmusSchema = z.object({
  direction: z.enum(["derecha", "izquierda", "up-beating", "down-beating", "ninguno"]).optional(),
  spv: z.coerce.number().min(0).max(50).optional(),
  durationSec: z.coerce.number().min(0).max(300).optional(),
  latencySec: z.coerce.number().min(0).max(30).optional(),
  fatigable: z.boolean().optional(),
});

const positionalsSchema = z.object({
  dixHallpikeRight: positionalNystagmusSchema.optional(),
  dixHallpikeLeft: positionalNystagmusSchema.optional(),
  rollTestRight: positionalNystagmusSchema.optional(),
  rollTestLeft: positionalNystagmusSchema.optional(),
  supine: positionalNystagmusSchema.optional(),
  headHanging: positionalNystagmusSchema.optional(),
  sitting: positionalNystagmusSchema.optional(),
});

// ─── Oculomotor ──────────────────────────────────────

const saccadesSchema = z.object({
  latency: z.coerce.number().min(100).max(600).optional(),
  accuracy: z.coerce.number().min(0).max(1.5).optional(),
  peakVelocity: z.coerce.number().min(50).max(800).optional(),
});

const smoothPursuitSchema = z.object({
  gain: z.coerce.number().min(0).max(1.2).optional(),
  type: z.enum(["sinusoidal", "sacadico", "ataxico"]).optional(),
});

const optokineticSchema = z.object({
  gainRight: z.coerce.number().min(0).max(1.5).optional(),
  gainLeft: z.coerce.number().min(0).max(1.5).optional(),
});

const oculomotorSchema = z.object({
  saccades: saccadesSchema.optional(),
  smoothPursuit: smoothPursuitSchema.optional(),
  optokinetic: optokineticSchema.optional(),
});

// ─── Schema principal ────────────────────────────────

export const vngSchema = z.object({
  spontaneous: spontaneousSchema.optional(),
  caloric: caloricSchema.optional(),
  positionals: positionalsSchema.optional(),
  oculomotor: oculomotorSchema.optional(),
  observaciones: z.string().optional(),
});

export type VNGData = z.infer<typeof vngSchema>;
export type SpontaneousConfig = z.infer<typeof spontaneousSchema>;
export type CaloricConfig = z.infer<typeof caloricSchema>;
export type PositionalsConfig = z.infer<typeof positionalsSchema>;
export type PositionalNystagmus = z.infer<typeof positionalNystagmusSchema>;
export type OculomotorConfig = z.infer<typeof oculomotorSchema>;
