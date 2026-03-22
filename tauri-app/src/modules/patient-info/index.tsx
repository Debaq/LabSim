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
    "identity", patientInfoSchema, "Datos del paciente",
  );
  const { register, handleSubmit, setValue, watch, formState: { errors } } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <User className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold ls-text">
            Datos del Paciente
          </h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />
          Guardar
        </Button>
      </div>

      {/* Personal Info */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Información Personal
        </legend>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="firstName" className="ls-text2">
              Nombre *
            </Label>
            <Input
              id="firstName"
              {...register("firstName")}
              className="ls-border ls-bg-input ls-text"
              placeholder="Nombre"
            />
            {errors.firstName && (
              <p className="text-xs text-red-400">{errors.firstName.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="lastName" className="ls-text2">
              Apellido *
            </Label>
            <Input
              id="lastName"
              {...register("lastName")}
              className="ls-border ls-bg-input ls-text"
              placeholder="Apellido"
            />
            {errors.lastName && (
              <p className="text-xs text-red-400">{errors.lastName.message}</p>
            )}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="documentId" className="ls-text2">
              Documento
            </Label>
            <Input
              id="documentId"
              {...register("documentId")}
              className="ls-border ls-bg-input ls-text"
              placeholder="RUT / DNI / CI"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="birthDate" className="ls-text2">
              Fecha de Nacimiento
            </Label>
            <Input
              id="birthDate"
              type="date"
              {...register("birthDate")}
              className="ls-border ls-bg-input ls-text"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="age" className="ls-text2">
              Edad
            </Label>
            <Input
              id="age"
              type="number"
              min={0}
              max={150}
              {...register("age")}
              className="ls-border ls-bg-input ls-text"
              placeholder="Años"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label className="ls-text2">Género</Label>
          <Select
            value={watch("gender") ?? ""}
            onValueChange={(val) =>
              setValue("gender", val as PatientInfoData["gender"], {
                shouldDirty: true,
              })
            }
          >
            <SelectTrigger className="ls-border ls-bg-input ls-text">
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
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Contacto
        </legend>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="phone" className="ls-text2">
              Teléfono
            </Label>
            <Input
              id="phone"
              type="tel"
              {...register("phone")}
              className="ls-border ls-bg-input ls-text"
              placeholder="+56 9 1234 5678"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="email" className="ls-text2">
              Email
            </Label>
            <Input
              id="email"
              type="email"
              {...register("email")}
              className="ls-border ls-bg-input ls-text"
              placeholder="paciente@email.com"
            />
            {errors.email && (
              <p className="text-xs text-red-400">{errors.email.message}</p>
            )}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="address" className="ls-text2">
              Dirección
            </Label>
            <Input
              id="address"
              {...register("address")}
              className="ls-border ls-bg-input ls-text"
              placeholder="Calle, número"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="city" className="ls-text2">
              Ciudad
            </Label>
            <Input
              id="city"
              {...register("city")}
              className="ls-border ls-bg-input ls-text"
              placeholder="Ciudad"
            />
          </div>
        </div>
      </fieldset>

      {/* Professional Info */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Información Clínica
        </legend>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="occupation" className="ls-text2">
              Ocupación
            </Label>
            <Input
              id="occupation"
              {...register("occupation")}
              className="ls-border ls-bg-input ls-text"
              placeholder="Ocupación actual"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="referredBy" className="ls-text2">
              Derivado por
            </Label>
            <Input
              id="referredBy"
              {...register("referredBy")}
              className="ls-border ls-bg-input ls-text"
              placeholder="Médico / Institución"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="healthInsurance" className="ls-text2">
            Previsión de Salud
          </Label>
          <Input
            id="healthInsurance"
            {...register("healthInsurance")}
            className="ls-border ls-bg-input ls-text"
            placeholder="Fonasa / Isapre / Particular"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="notes" className="ls-text2">
            Observaciones
          </Label>
          <Textarea
            id="notes"
            {...register("notes")}
            className="min-h-20 ls-border ls-bg-input ls-text"
            placeholder="Notas adicionales..."
          />
        </div>
      </fieldset>
    </form>
  );
}
