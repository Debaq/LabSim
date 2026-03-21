import { z } from "zod/v4";

export const patientInfoSchema = z.object({
  firstName: z.string().min(1, "Nombre requerido"),
  lastName: z.string().min(1, "Apellido requerido"),
  documentId: z.string().optional(),
  birthDate: z.string().optional(),
  age: z.coerce.number().min(0).max(150).optional(),
  gender: z.enum(["male", "female", "other"]).optional(),
  phone: z.string().optional(),
  email: z.email("Email inválido").optional().or(z.literal("")),
  address: z.string().optional(),
  city: z.string().optional(),
  occupation: z.string().optional(),
  referredBy: z.string().optional(),
  healthInsurance: z.string().optional(),
  notes: z.string().optional(),
});

export type PatientInfoData = z.infer<typeof patientInfoSchema>;
