import { z } from "zod/v4";

/**
 * Schema de datos fisiológicos del oído para impedanciometría.
 *
 * Estos NO son resultados del examen — son los parámetros reales del oído
 * que el generador sintético usa para producir las curvas.
 * El docente configura esto al crear el paciente.
 * El estudiante nunca ve estos datos directamente — solo ve la curva en el equipo.
 */

const earPhysiologySchema = z.object({
  // ─── Timpanometría ─────────────────────────────
  /** Compliance estática real del oído medio (ml). Normal: 0.3-1.6 */
  compliancePeak: z.coerce.number().min(0).max(10).optional(),
  /** Presión del oído medio real (daPa). Normal: -50 a +50 */
  middleEarPressure: z.coerce.number().min(-600).max(400).optional(),
  /** Volumen del canal auditivo externo (ml). Normal: 0.6-2.0 adultos */
  earCanalVolume: z.coerce.number().min(0).max(10).optional(),
  /** Ancho de la curva a 50% del pico (daPa). Normal: 60-150 */
  tympWidth: z.coerce.number().min(0).max(400).optional(),
  /** Si hay perforación timpánica (volumen alto, sin pico) */
  perforated: z.boolean().optional(),

  // ─── Reflejos acústicos ────────────────────────
  /** Umbrales de reflejo ipsilateral por frecuencia (dB HL). null = ausente */
  reflexIpsi500: z.coerce.number().min(50).max(120).nullable().optional(),
  reflexIpsi1000: z.coerce.number().min(50).max(120).nullable().optional(),
  reflexIpsi2000: z.coerce.number().min(50).max(120).nullable().optional(),
  reflexIpsi4000: z.coerce.number().min(50).max(120).nullable().optional(),
  /** Umbrales de reflejo contralateral por frecuencia (dB HL). null = ausente */
  reflexContra500: z.coerce.number().min(50).max(120).nullable().optional(),
  reflexContra1000: z.coerce.number().min(50).max(120).nullable().optional(),
  reflexContra2000: z.coerce.number().min(50).max(120).nullable().optional(),
  reflexContra4000: z.coerce.number().min(50).max(120).nullable().optional(),

  // ─── Deterioro del reflejo ─────────────────────
  /** Porcentaje de decaimiento a 500 Hz en 10s. >50% = patológico */
  reflexDecay500: z.coerce.number().min(0).max(100).optional(),
  /** Porcentaje de decaimiento a 1000 Hz en 10s */
  reflexDecay1000: z.coerce.number().min(0).max(100).optional(),

  // ─── Función tubárica ──────────────────────────
  /** Desplazamiento de presión con Toynbee (daPa). Normal: -10 a -30 */
  toynbeeShift: z.coerce.number().min(-100).max(100).optional(),
  /** Desplazamiento de presión con Valsalva (daPa). Normal: +10 a +30 */
  valsalvaShift: z.coerce.number().min(-100).max(100).optional(),
});

export const impedanceSchema = z.object({
  oidoDerecho: earPhysiologySchema.optional(),
  oidoIzquierdo: earPhysiologySchema.optional(),
  /** Varianza natural para realismo (0-1). 0=perfecto, 1=mucha variación */
  naturalVariance: z.coerce.number().min(0).max(1).optional(),
  observaciones: z.string().optional(),
});

export type ImpedanceData = z.infer<typeof impedanceSchema>;
export type EarPhysiology = z.infer<typeof earPhysiologySchema>;
