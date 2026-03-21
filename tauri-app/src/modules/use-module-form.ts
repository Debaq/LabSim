import { useEffect } from "react";
import { useForm, type DefaultValues, type FieldValues } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { usePatientStore, type PatientData } from "@/stores/patient-store";
import { toast } from "sonner";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function useModuleForm<T extends FieldValues>(
  moduleKey: keyof PatientData,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  schema: any,
  moduleName: string,
) {
  const storedData = usePatientStore((s) => s.data[moduleKey]);
  const updateModule = usePatientStore((s) => s.updateModule);

  const form = useForm<T>({
    resolver: zodResolver(schema),
    defaultValues: (Object.keys(storedData).length > 0
      ? storedData
      : undefined) as DefaultValues<T>,
  });

  const { watch, formState: { isDirty } } = form;
  const values = watch();

  // Auto-save debounced
  useEffect(() => {
    if (!isDirty) return;
    const t = setTimeout(() => {
      updateModule(moduleKey, values as Record<string, unknown>);
    }, 1500);
    return () => clearTimeout(t);
  }, [values, isDirty, updateModule, moduleKey]);

  const onSubmit = (data: FieldValues) => {
    updateModule(moduleKey, data as Record<string, unknown>);
    toast.success(`${moduleName} guardado`);
  };

  return { form, onSubmit };
}
