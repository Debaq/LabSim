import { useEffect, useRef } from "react";
import { useForm, type DefaultValues, type FieldValues } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { usePatientStore, type PatientCore } from "@/stores/patient-store";
import { toast } from "sonner";

const CORE_KEYS = new Set<string>(["identity", "personality", "clinicalHistory"]);
const EMPTY: Record<string, unknown> = {};

/**
 * Hook de formulario para módulos del paciente.
 *
 * - Si moduleKey es "identity", "personality", o "clinicalHistory" → lee/escribe en data.core
 * - Si es cualquier otra cosa (audiometry, oct, etc.) → lee/escribe en data.modules
 *
 * Esto permite agregar nuevos simuladores sin tocar este hook.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function useModuleForm<T extends FieldValues>(
  moduleKey: string,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  schema: any,
  moduleName: string,
) {
  const isCore = CORE_KEYS.has(moduleKey);

  const storedData = usePatientStore((s) =>
    isCore
      ? (s.data.core[moduleKey as keyof PatientCore] ?? EMPTY)
      : (s.data.modules[moduleKey] ?? EMPTY),
  );
  const updateCore = usePatientStore((s) => s.updateCore);
  const updateModule = usePatientStore((s) => s.updateModule);

  const form = useForm<T>({
    resolver: zodResolver(schema),
    defaultValues: (Object.keys(storedData).length > 0
      ? storedData
      : undefined) as DefaultValues<T>,
  });

  const { watch, formState: { isDirty } } = form;

  // Auto-save debounced — usar ref para evitar que watch() dispare re-renders infinitos
  const valuesRef = useRef<FieldValues>({});
  useEffect(() => {
    const sub = watch((v) => { valuesRef.current = v; });
    return () => sub.unsubscribe();
  }, [watch]);

  useEffect(() => {
    if (!isDirty) return;
    const t = setTimeout(() => {
      const v = valuesRef.current;
      if (isCore) {
        updateCore(moduleKey as keyof PatientCore, v as Record<string, unknown>);
      } else {
        updateModule(moduleKey, v as Record<string, unknown>);
      }
    }, 1500);
    return () => clearTimeout(t);
  }, [isDirty, updateCore, updateModule, moduleKey, isCore]);

  const onSubmit = (data: FieldValues) => {
    if (isCore) {
      updateCore(moduleKey as keyof PatientCore, data as Record<string, unknown>);
    } else {
      updateModule(moduleKey, data as Record<string, unknown>);
    }
    toast.success(`${moduleName} guardado`);
  };

  return { form, onSubmit };
}
