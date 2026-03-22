# Cómo Agregar un Nuevo Simulador

La arquitectura de pacientes es **modular por diseño**. Agregar un nuevo simulador (ej: otoscopía, espirometría, ECG) no requiere tocar el core del sistema.

## Pasos

### 1. Crear el schema del módulo

```
src/modules/{id}/schema.ts
```

Define los datos fisiológicos del paciente para este examen. Solo datos reales — no resultados, no artefactos (esos van en la agenda).

```typescript
import { z } from "zod/v4";

export const otoscopySchema = z.object({
  rightEar: z.object({
    tympanicMembrane: z.enum(["normal", "perforated", "retracted", "bulging"]).optional(),
    // ... más campos
  }).optional(),
  leftEar: z.object({ /* ... */ }).optional(),
  observaciones: z.string().optional(),
});

export type OtoscopyData = z.infer<typeof otoscopySchema>;
```

### 2. Crear el formulario del módulo

```
src/modules/{id}/index.tsx
```

El formulario que el docente usa para configurar el paciente:

```typescript
export default function OtoscopyModule() {
  const { form, onSubmit } = useModuleForm<OtoscopyData>(
    "otoscopy", otoscopySchema, "Otoscopía",
  );
  // ... formulario con campos
}
```

### 3. Crear el generador sintético (si aplica)

```
src/lib/{id}-synthetic.ts
```

Genera datos realistas a partir de los parámetros fisiológicos.

### 4. Crear la ventana del simulador

```
src/components/windows/{id}-window.tsx
```

La UI del equipo. Incluir `<PatientBanner simulatorName="Otoscopio" />` para el banner de paciente activo.

### 5. Registrar

En `src/lib/constants.ts`:
```typescript
// Agregar a MODULE_IDS
"otoscopy",

// Agregar a MODULE_LABELS
otoscopy: "Otoscopía",

// Agregar a MODULE_STORE_KEYS
otoscopy: { type: "module", key: "otoscopy" },
```

En `src/components/clinical/module-loader.tsx`:
```typescript
otoscopy: lazy(() => import("@/modules/otoscopy")),
```

En `src/components/windows/window-content.tsx`:
```typescript
import { OtoscopyWindow } from "./otoscopy-window";
// ...
"otoscopy": OtoscopyWindow,
```

En `src/components/layout/desktop-area.tsx` agregar el icono.

### 6. Listo

No se toca `patient-store.ts`, no se toca el backend, no se modifica ningún otro simulador. El nuevo módulo se guarda automáticamente en `data.modules.otoscopy` del paciente.
