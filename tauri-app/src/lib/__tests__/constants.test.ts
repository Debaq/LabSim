import { describe, it, expect } from 'vitest'
import {
  ISO_FREQUENCIES,
  EXTENDED_FREQUENCIES,
  THRESHOLD_MIN,
  THRESHOLD_MAX,
  THRESHOLD_STEP,
  TIMPANOMETRY_PRESSURE_MIN,
  TIMPANOMETRY_PRESSURE_MAX,
  MODULE_IDS,
  MODULE_LABELS,
} from '../constants'

describe('ISO_FREQUENCIES', () => {
  it('debe contener las frecuencias audiométricas estándar', () => {
    expect(ISO_FREQUENCIES).toContain(250)
    expect(ISO_FREQUENCIES).toContain(500)
    expect(ISO_FREQUENCIES).toContain(1000)
    expect(ISO_FREQUENCIES).toContain(2000)
    expect(ISO_FREQUENCIES).toContain(4000)
    expect(ISO_FREQUENCIES).toContain(8000)
  })

  it('debe tener 11 frecuencias', () => {
    expect(ISO_FREQUENCIES).toHaveLength(11)
  })

  it('debe comenzar en 125 Hz y terminar en 8000 Hz', () => {
    expect(ISO_FREQUENCIES[0]).toBe(125)
    expect(ISO_FREQUENCIES[ISO_FREQUENCIES.length - 1]).toBe(8000)
  })

  it('debe estar ordenado de menor a mayor', () => {
    for (let i = 1; i < ISO_FREQUENCIES.length; i++) {
      expect(ISO_FREQUENCIES[i]).toBeGreaterThan(ISO_FREQUENCIES[i - 1])
    }
  })
})

describe('EXTENDED_FREQUENCIES', () => {
  it('debe incluir todas las frecuencias ISO', () => {
    for (const freq of ISO_FREQUENCIES) {
      expect(EXTENDED_FREQUENCIES).toContain(freq)
    }
  })

  it('debe incluir frecuencias extendidas hasta 20000 Hz', () => {
    expect(EXTENDED_FREQUENCIES).toContain(10000)
    expect(EXTENDED_FREQUENCIES).toContain(12000)
    expect(EXTENDED_FREQUENCIES).toContain(16000)
    expect(EXTENDED_FREQUENCIES).toContain(20000)
  })
})

describe('Constantes de umbral', () => {
  it('debe tener un rango de umbral de -10 a 120 dB', () => {
    expect(THRESHOLD_MIN).toBe(-10)
    expect(THRESHOLD_MAX).toBe(120)
  })

  it('debe tener un paso de 5 dB', () => {
    expect(THRESHOLD_STEP).toBe(5)
  })
})

describe('Constantes de timpanometría', () => {
  it('debe tener un rango de presión de -400 a 200 daPa', () => {
    expect(TIMPANOMETRY_PRESSURE_MIN).toBe(-400)
    expect(TIMPANOMETRY_PRESSURE_MAX).toBe(200)
  })
})

describe('MODULE_IDS', () => {
  it('debe tener 12 entradas', () => {
    expect(MODULE_IDS).toHaveLength(12)
  })

  it('debe contener todos los módulos esperados', () => {
    const expectedModules = [
      'patient-info',
      'anamnesis',
      'audiometry',
      'logoaudiometry',
      'supraliminal',
      'impedance',
      'oae',
      'abr',
      'electrocochleo',
      'hearing-aids',
      'agenda',
      'json-output',
    ]

    for (const mod of expectedModules) {
      expect(MODULE_IDS).toContain(mod)
    }
  })
})

describe('MODULE_LABELS', () => {
  it('debe tener una etiqueta para cada MODULE_ID', () => {
    for (const id of MODULE_IDS) {
      expect(MODULE_LABELS[id]).toBeDefined()
      expect(typeof MODULE_LABELS[id]).toBe('string')
      expect(MODULE_LABELS[id].length).toBeGreaterThan(0)
    }
  })

  it('debe mapear correctamente los módulos principales', () => {
    expect(MODULE_LABELS['patient-info']).toBe('Datos del Paciente')
    expect(MODULE_LABELS['audiometry']).toBe('Audiometría')
    expect(MODULE_LABELS['impedance']).toBe('Impedanciometría')
    expect(MODULE_LABELS['oae']).toBe('Emisiones Otoacústicas')
    expect(MODULE_LABELS['abr']).toBe('Potenciales Evocados')
    expect(MODULE_LABELS['hearing-aids']).toBe('Audífonos')
  })

  it('debe mapear correctamente anamnesis y agenda', () => {
    expect(MODULE_LABELS['anamnesis']).toBe('Anamnesis')
    expect(MODULE_LABELS['agenda']).toBe('Agenda')
  })

  it('debe mapear correctamente json-output', () => {
    expect(MODULE_LABELS['json-output']).toBe('Exportar JSON')
  })
})
