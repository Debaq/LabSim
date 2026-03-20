import { useModuleForm } from "@/modules/use-module-form";
import { patientInfoSchema, type PatientInfoData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Save, User } from "lucide-react";

export default function PatientInfoModule() {
  const { form, onSubmit } = useModuleForm<PatientInfoData>(
    "patientInfo", patientInfoSchema, "Datos del paciente",
  );
  const { register, handleSubmit, setValue, watch, formState: { errors } } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <User className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">
            Datos del Paciente
          </h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />
          Guardar
        </Button>
      </div>

      {/* Personal Info */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          Información Personal
        </legend>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="firstName" className="text-white/70">
              Nombre *
            </Label>
            <Input
              id="firstName"
              {...register("firstName")}
              className="border-white/10 bg-white/5 text-white"
              placeholder="Nombre"
            />
            {errors.firstName && (
              <p className="text-xs text-red-400">{errors.firstName.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="lastName" className="text-white/70">
              Apellido *
            </Label>
            <Input
              id="lastName"
              {...register("lastName")}
              className="border-white/10 bg-white/5 text-white"
              placeholder="Apellido"
            />
            {errors.lastName && (
              <p className="text-xs text-red-400">{errors.lastName.message}</p>
            )}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="documentId" className="text-white/70">
              Documento
            </Label>
            <Input
              id="documentId"
              {...register("documentId")}
              className="border-white/10 bg-white/5 text-white"
              placeholder="RUT / DNI / CI"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="birthDate" className="text-white/70">
              Fecha de Nacimiento
            </Label>
            <Input
              id="birthDate"
              type="date"
              {...register("birthDate")}
              className="border-white/10 bg-white/5 text-white"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="age" className="text-white/70">
              Edad
            </Label>
            <Input
              id="age"
              type="number"
              min={0}
              max={150}
              {...register("age")}
              className="border-white/10 bg-white/5 text-white"
              placeholder="Años"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label className="text-white/70">Género</Label>
          <Select
            value={watch("gender") ?? ""}
            onValueChange={(val) =>
              setValue("gender", val as PatientInfoData["gender"], {
                shouldDirty: true,
              })
            }
          >
            <SelectTrigger className="border-white/10 bg-white/5 text-white">
              <SelectValue placeholder="Seleccionar" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="male">Masculino</SelectItem>
              <SelectItem value="female">Femenino</SelectItem>
              <SelectItem value="other">Otro</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </fieldset>

      {/* Contact Info */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          Contacto
        </legend>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="phone" className="text-white/70">
              Teléfono
            </Label>
            <Input
              id="phone"
              type="tel"
              {...register("phone")}
              className="border-white/10 bg-white/5 text-white"
              placeholder="+56 9 1234 5678"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="email" className="text-white/70">
              Email
            </Label>
            <Input
              id="email"
              type="email"
              {...register("email")}
              className="border-white/10 bg-white/5 text-white"
              placeholder="paciente@email.com"
            />
            {errors.email && (
              <p className="text-xs text-red-400">{errors.email.message}</p>
            )}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="address" className="text-white/70">
              Dirección
            </Label>
            <Input
              id="address"
              {...register("address")}
              className="border-white/10 bg-white/5 text-white"
              placeholder="Calle, número"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="city" className="text-white/70">
              Ciudad
            </Label>
            <Input
              id="city"
              {...register("city")}
              className="border-white/10 bg-white/5 text-white"
              placeholder="Ciudad"
            />
          </div>
        </div>
      </fieldset>

      {/* Professional Info */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          Información Clínica
        </legend>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="occupation" className="text-white/70">
              Ocupación
            </Label>
            <Input
              id="occupation"
              {...register("occupation")}
              className="border-white/10 bg-white/5 text-white"
              placeholder="Ocupación actual"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="referredBy" className="text-white/70">
              Derivado por
            </Label>
            <Input
              id="referredBy"
              {...register("referredBy")}
              className="border-white/10 bg-white/5 text-white"
              placeholder="Médico / Institución"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="healthInsurance" className="text-white/70">
            Previsión de Salud
          </Label>
          <Input
            id="healthInsurance"
            {...register("healthInsurance")}
            className="border-white/10 bg-white/5 text-white"
            placeholder="Fonasa / Isapre / Particular"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="notes" className="text-white/70">
            Observaciones
          </Label>
          <Textarea
            id="notes"
            {...register("notes")}
            className="min-h-20 border-white/10 bg-white/5 text-white"
            placeholder="Notas adicionales..."
          />
        </div>
      </fieldset>
    </form>
  );
}
