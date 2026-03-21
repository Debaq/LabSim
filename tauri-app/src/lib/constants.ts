export const ISO_FREQUENCIES = [125, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000] as const;

export const EXTENDED_FREQUENCIES = [...ISO_FREQUENCIES, 10000, 12000, 14000, 16000, 20000] as const;

export const THRESHOLD_MIN = -10;
export const THRESHOLD_MAX = 120;
export const THRESHOLD_STEP = 5;

export const TIMPANOMETRY_PRESSURE_MIN = -400;
export const TIMPANOMETRY_PRESSURE_MAX = 200;

export const MODULE_IDS = [
  "patient-info",
  "anamnesis",
  "audiometry",
  "logoaudiometry",
  "supraliminal",
  "impedance",
  "oae",
  "abr",
  "electrocochleo",
  "hearing-aids",
  "oct",
  "visual-field",
  "agenda",
  "json-output",
] as const;

export type ModuleId = (typeof MODULE_IDS)[number];

export const MODULE_LABELS: Record<ModuleId, string> = {
  "patient-info": "Datos del Paciente",
  anamnesis: "Anamnesis",
  audiometry: "Audiometría",
  logoaudiometry: "Logoaudiometría",
  supraliminal: "Supraliminal",
  impedance: "Impedanciometría",
  oae: "Emisiones Otoacústicas",
  abr: "Potenciales Evocados",
  electrocochleo: "Electrococleografía",
  "hearing-aids": "Audífonos",
  oct: "OCT",
  "visual-field": "Campo Visual",
  agenda: "Agenda",
  "json-output": "Exportar JSON",
};
