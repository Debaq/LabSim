import { z } from "zod";

const eyeSchema = z.object({
  patologia: z.enum([
    "normal",
    "retinopatia-diabetica-npdr",
    "retinopatia-diabetica-pdr",
    "degeneracion-macular-seca",
    "degeneracion-macular-humeda",
    "desprendimiento-retina",
    "oclusion-vena-central",
    "oclusion-arteria-central",
    "papilledema",
    "glaucoma-excavacion",
    "nevus-coroideo",
    "membrana-epirretinal",
    "agujero-macular",
  ]).optional(),
  severidad: z.enum(["leve", "moderado", "severo"]).optional(),
  calidadImagen: z.coerce.number().min(1).max(10).optional(),
  notas: z.string().optional(),
});

export const retinographySchema = z.object({
  ojoDerecho: eyeSchema.optional(),
  ojoIzquierdo: eyeSchema.optional(),
  observaciones: z.string().optional(),
});

export type RetinographyData = z.infer<typeof retinographySchema>;
