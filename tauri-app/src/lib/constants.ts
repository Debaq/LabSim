export const ISO_FREQUENCIES = [125, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000] as const;

export const EXTENDED_FREQUENCIES = [...ISO_FREQUENCIES, 10000, 12000, 14000, 16000, 20000] as const;

export const THRESHOLD_MIN = -10;
export const THRESHOLD_MAX = 120;
export const THRESHOLD_STEP = 5;

export const TIMPANOMETRY_PRESSURE_MIN = -400;
export const TIMPANOMETRY_PRESSURE_MAX = 200;

/**
 * Módulos del editor de pacientes.
 *
 * Core: patient-info, patient-personality, anamnesis (datos fijos del paciente)
 * Clínicos: audiometry, oct, etc. (extensibles — agregar nuevos sin tocar el core)
 *
 * Para agregar un nuevo simulador:
 * 1. Crear directorio en src/modules/{id}/
 * 2. Agregar el ID aquí
 * 3. Agregar label en MODULE_LABELS
 * 4. Agregar lazy import en module-loader.tsx
 */
export const MODULE_IDS = [
  // Core del paciente
  "patient-info",
  "patient-personality",
  "anamnesis",
  // Módulos clínicos (simuladores)
  "audiometry",
  "tuning-fork",
  "logoaudiometry",
  "supraliminal",
  "impedance",
  "oae",
  "abr",
  "electrocochleo",
  "hearing-aids",
  "oct",
  "visual-field",
  "corneal-topography",
  "retinography",
  "scheimpflug",
  "vng",
  "vhit",
] as const;

export type ModuleId = (typeof MODULE_IDS)[number];

export const MODULE_LABELS: Record<ModuleId, string> = {
  "patient-info": "Datos del Paciente",
  "patient-personality": "Personalidad",
  anamnesis: "Historia Clínica",
  audiometry: "Audiometría",
  "tuning-fork": "Acumetría",
  logoaudiometry: "Logoaudiometría",
  supraliminal: "Supraliminal",
  impedance: "Impedanciometría",
  oae: "Emisiones Otoacústicas",
  abr: "Potenciales Evocados",
  electrocochleo: "Electrococleografía",
  "hearing-aids": "Audífonos",
  oct: "OCT",
  "visual-field": "Campo Visual",
  "corneal-topography": "Topografía Corneal",
  retinography: "Retinografía",
  scheimpflug: "Scheimpflug",
  vng: "VNG",
  vhit: "vHIT",
};

/**
 * Mapeo de ModuleId del editor → key en PatientData.
 * Core modules mapean a data.core[storeKey].
 * Clinical modules mapean a data.modules[storeKey].
 */
export const MODULE_STORE_KEYS: Record<ModuleId, { type: "core" | "module"; key: string }> = {
  "patient-info": { type: "core", key: "identity" },
  "patient-personality": { type: "core", key: "personality" },
  anamnesis: { type: "core", key: "clinicalHistory" },
  audiometry: { type: "module", key: "audiometry" },
  "tuning-fork": { type: "module", key: "tuningFork" },
  logoaudiometry: { type: "module", key: "logoaudiometry" },
  supraliminal: { type: "module", key: "supraliminal" },
  impedance: { type: "module", key: "impedance" },
  oae: { type: "module", key: "oae" },
  abr: { type: "module", key: "abr" },
  electrocochleo: { type: "module", key: "electrocochleo" },
  "hearing-aids": { type: "module", key: "hearingAids" },
  oct: { type: "module", key: "oct" },
  "visual-field": { type: "module", key: "visualField" },
  "corneal-topography": { type: "module", key: "cornealTopography" },
  retinography: { type: "module", key: "retinography" },
  scheimpflug: { type: "module", key: "scheimpflug" },
  vng: { type: "module", key: "vng" },
  vhit: { type: "module", key: "vhit" },
};
