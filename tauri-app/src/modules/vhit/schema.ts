import { z } from "zod/v4";

/**
 * Schema de datos fisiológicos para vHIT (Video Head Impulse Test).
 *
 * Evalúa los 6 canales semicirculares con impulsos cefálicos rápidos.
 * El docente define: ganancia VOR, tipo de sacadas correctivas, y artefactos.
 */

export const SEVERITIES = ["leve", "moderado", "severo"] as const;

/**
 * Configuración por canal semicircular.
 */
const canalConfig = z.object({
  /** Ganancia VOR. Normal: 0.8-1.2 */
  gain: z.coerce.number().min(0).max(1.5).optional(),
  /** Tiene sacadas overt (durante el impulso). Típico en lesión aguda */
  hasOvertSaccades: z.boolean().optional(),
  /** Tiene sacadas covert (después del impulso). Típico en lesión compensada */
  hasCovertSaccades: z.boolean().optional(),
  /** Proporción de impulsos con overt (0-1). No todos los impulsos tienen sacada */
  overtRate: z.coerce.number().min(0).max(1).optional(),
  /** Proporción de impulsos con covert (0-1) */
  covertRate: z.coerce.number().min(0).max(1).optional(),
});

const vhitConfig = z.object({
  severidad: z.enum(SEVERITIES).default("moderado"),

  // ─── 6 canales semicirculares ──────────────────
  lateralRight: canalConfig.optional(),
  lateralLeft: canalConfig.optional(),
  anteriorRight: canalConfig.optional(),   // LARP
  posteriorLeft: canalConfig.optional(),    // LARP
  anteriorLeft: canalConfig.optional(),     // RALP
  posteriorRight: canalConfig.optional(),   // RALP

  notas: z.string().optional(),
});

export const vhitSchema = z.object({
  datos: vhitConfig.optional(),
  observaciones: z.string().optional(),
});

export type VHITData = z.infer<typeof vhitSchema>;
export type VHITConfig = z.infer<typeof vhitConfig>;
export type CanalConfig = z.infer<typeof canalConfig>;
