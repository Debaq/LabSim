import { z } from "zod";

export const personalitySchema = z.object({
  displayName: z.string().optional(),
  age: z.coerce.number().min(0).max(120).optional(),
  personalityType: z.string().optional(),
  communicationStyle: z.string().optional(),
  toneOfVoice: z.string().optional(),
  backstory: z.string().optional(),
  /** Nivel de cooperación en exámenes del PERSONAJE: total/parcial/difícil.
   * Esto es la personalidad, no la sesión.
   * El nivel numérico por sesión va en la agenda. */
  examCooperation: z.string().optional(),

  // ─── Voz del paciente ─────────────────────────────
  /** ID de la voz TTS: "male" | "female" */
  voiceId: z.string().optional(),
  /** Desplazamiento de tono en semitonos (-4 a +4). Cada semitono ≈ 6% de cambio. */
  pitchShift: z.coerce.number().min(-4).max(4).optional(),
  /** Factor de velocidad del habla (0.75 a 1.3). 1.0 = normal. */
  speechRate: z.coerce.number().min(0.75).max(1.3).optional(),
});

export type PersonalityData = z.infer<typeof personalitySchema>;
