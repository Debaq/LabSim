/**
 * Configuración de sesión de una cita (agenda_item).
 *
 * Estos datos los configura el DOCENTE al crear la agenda.
 * El ESTUDIANTE no los ve — solo los experimenta.
 *
 * Controla: cooperación del paciente, artefactos por equipo,
 * y cualquier condición de la sesión que no es propia del paciente.
 */

export interface SessionConfig {
  // ─── Cooperación general del paciente ──────────
  /** Nivel de cooperación (0-1). Afecta todos los equipos */
  cooperationLevel?: number;

  // ─── Artefactos por equipo ─────────────────────

  /** Impedanciometría */
  impedance?: {
    /** Fuga de aire en la sonda (0-1) */
    probeSealFailRate?: number;
  };

  /** Campo Visual */
  perimetry?: {
    /** Tasa extra de falsos positivos */
    extraFalsePositiveRate?: number;
    /** Tasa extra de falsos negativos */
    extraFalseNegativeRate?: number;
    /** Tasa extra de pérdida de fijación */
    extraFixationLossRate?: number;
    /** Factor extra de fatiga */
    extraFatigue?: number;
  };

  /** OCT */
  oct?: {
    /** Calidad de lágrima (0-1). Baja = señal degradada */
    tearFilmQuality?: number;
    /** Artefactos de movimiento (0-1) */
    motionArtifactRate?: number;
    /** Parpadeo frecuente (0-1) */
    blinkRate?: number;
  };

  /** Topografía corneal (Placido) */
  cornealTopography?: {
    tearFilmQuality?: number;
    /** Artefactos de descentramiento (0-1) */
    decentrationRate?: number;
  };

  /** Scheimpflug */
  scheimpflug?: {
    tearFilmQuality?: number;
    motionArtifactRate?: number;
  };

  /** Retinografía */
  retinography?: {
    /** Midriasis insuficiente — pupilas pequeñas */
    poorMydriasis?: boolean;
    blinkRate?: number;
  };

  /** vHIT */
  vhit?: {
    /** Artefactos de gafas — slippage, bounce (0-1) */
    goggleArtifactRate?: number;
  };

  /** VNG */
  vng?: {
    /** Artefactos de gafas/electrodos */
    electrodeArtifactRate?: number;
  };

  /** Audiometría */
  audiometry?: {
    /** Ruido eléctrico en auriculares (0-1) */
    electricalNoiseRate?: number;
    /** Zumbido de masking mal calibrado */
    maskingArtifact?: boolean;
  };
}

/**
 * Lee la configuración de sesión del agenda_item actual.
 * Retorna un objeto vacío si no hay configuración.
 */
export function parseSessionConfig(json: string | null | undefined): SessionConfig {
  if (!json) return {};
  try {
    return JSON.parse(json) as SessionConfig;
  } catch {
    return {};
  }
}
