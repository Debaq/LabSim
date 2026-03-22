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
});

export type PersonalityData = z.infer<typeof personalitySchema>;
