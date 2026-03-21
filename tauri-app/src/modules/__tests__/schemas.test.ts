import { describe, it, expect } from 'vitest'
import { patientInfoSchema } from '../patient-info/schema'
import { audiometrySchema } from '../audiometry/schema'
import { impedanceSchema } from '../impedance/schema'

describe('patientInfoSchema', () => {
  it('debe validar datos completos correctos', () => {
    const validData = {
      firstName: 'María',
      lastName: 'González',
      documentId: '12345678',
      birthDate: '1990-05-15',
      age: 35,
      gender: 'female',
      phone: '+54 11 1234-5678',
      email: 'maria@example.com',
      address: 'Av. Corrientes 1234',
      city: 'Buenos Aires',
      occupation: 'Docente',
      referredBy: 'Dr. López',
      healthInsurance: 'OSDE',
      notes: 'Primera consulta',
    }

    const result = patientInfoSchema.safeParse(validData)
    expect(result.success).toBe(true)
  })

  it('debe validar con solo los campos requeridos', () => {
    const minimalData = {
      firstName: 'Juan',
      lastName: 'Pérez',
    }

    const result = patientInfoSchema.safeParse(minimalData)
    expect(result.success).toBe(true)
  })

  it('debe rechazar si falta firstName', () => {
    const invalidData = {
      lastName: 'Pérez',
    }

    const result = patientInfoSchema.safeParse(invalidData)
    expect(result.success).toBe(false)
  })

  it('debe rechazar si falta lastName', () => {
    const invalidData = {
      firstName: 'Juan',
    }

    const result = patientInfoSchema.safeParse(invalidData)
    expect(result.success).toBe(false)
  })

  it('debe rechazar firstName vacío', () => {
    const invalidData = {
      firstName: '',
      lastName: 'Pérez',
    }

    const result = patientInfoSchema.safeParse(invalidData)
    expect(result.success).toBe(false)
  })

  it('debe rechazar un email inválido', () => {
    const invalidData = {
      firstName: 'Juan',
      lastName: 'Pérez',
      email: 'no-es-email',
    }

    const result = patientInfoSchema.safeParse(invalidData)
    expect(result.success).toBe(false)
  })

  it('debe aceptar email vacío', () => {
    const validData = {
      firstName: 'Juan',
      lastName: 'Pérez',
      email: '',
    }

    const result = patientInfoSchema.safeParse(validData)
    expect(result.success).toBe(true)
  })

  it('debe rechazar una edad fuera de rango', () => {
    const invalidData = {
      firstName: 'Juan',
      lastName: 'Pérez',
      age: 200,
    }

    const result = patientInfoSchema.safeParse(invalidData)
    expect(result.success).toBe(false)
  })

  it('debe rechazar un género no válido', () => {
    const invalidData = {
      firstName: 'Juan',
      lastName: 'Pérez',
      gender: 'invalid',
    }

    const result = patientInfoSchema.safeParse(invalidData)
    expect(result.success).toBe(false)
  })
})

describe('audiometrySchema', () => {
  it('debe validar datos de audiometría vacíos (defaults)', () => {
    const result = audiometrySchema.safeParse({
      umbralesAereos: {},
      umbralesOseos: {},
      ldl: {},
    })
    expect(result.success).toBe(true)
  })

  it('debe validar umbrales aéreos con valores correctos', () => {
    const data = {
      umbralesAereos: {
        oidoDerecho: { '1000': 25, '2000': 30, '4000': 40 },
        oidoIzquierdo: { '1000': 20, '2000': 25 },
      },
      umbralesOseos: {},
      ldl: {},
    }

    const result = audiometrySchema.safeParse(data)
    expect(result.success).toBe(true)
  })

  it('debe aceptar valores nulos en umbrales', () => {
    const data = {
      umbralesAereos: {
        oidoDerecho: { '1000': null, '2000': 30 },
        oidoIzquierdo: {},
      },
      umbralesOseos: {},
      ldl: {},
    }

    const result = audiometrySchema.safeParse(data)
    expect(result.success).toBe(true)
  })

  it('debe aceptar observaciones opcionales', () => {
    const data = {
      umbralesAereos: {},
      umbralesOseos: {},
      ldl: {},
      observaciones: 'Paciente colaborador',
    }

    const result = audiometrySchema.safeParse(data)
    expect(result.success).toBe(true)
  })

  it('debe validar umbrales óseos', () => {
    const data = {
      umbralesAereos: {},
      umbralesOseos: {
        oidoDerecho: { '500': 10, '1000': 15 },
        oidoIzquierdo: { '500': 5 },
      },
      ldl: {},
    }

    const result = audiometrySchema.safeParse(data)
    expect(result.success).toBe(true)
  })
})

describe('impedanceSchema', () => {
  const emptyReflejos = {
    oidoDerecho: { ipsi: {}, contra: {} },
    oidoIzquierdo: { ipsi: {}, contra: {} },
  }

  it('debe validar datos de impedanciometría vacíos (defaults)', () => {
    const result = impedanceSchema.safeParse({
      timpanometria: {
        oidoDerecho: {},
        oidoIzquierdo: {},
      },
      reflejosAcusticos: emptyReflejos,
    })
    expect(result.success).toBe(true)
  })

  it('debe validar timpanometría con valores correctos', () => {
    const data = {
      timpanometria: {
        oidoDerecho: {
          complianceMaxima: 0.8,
          presion: -15,
          volumenEac: 1.2,
          gradiente: 80,
        },
        oidoIzquierdo: {
          complianceMaxima: 0.6,
          presion: -20,
          volumenEac: 1.0,
          gradiente: 75,
        },
      },
      reflejosAcusticos: emptyReflejos,
    }

    const result = impedanceSchema.safeParse(data)
    expect(result.success).toBe(true)
  })

  it('debe validar reflejos acústicos ipsi y contra', () => {
    const data = {
      timpanometria: {},
      reflejosAcusticos: {
        oidoDerecho: {
          ipsi: { '500': '85', '1000': '90', '2000': '95', '4000': '100' },
          contra: { '500': '90', '1000': '95' },
        },
        oidoIzquierdo: {
          ipsi: { '500': '80', '1000': '85' },
          contra: { '500': 'AUS', '1000': 'AUS' },
        },
      },
    }

    const result = impedanceSchema.safeParse(data)
    expect(result.success).toBe(true)
  })

  it('debe rechazar presión fuera de rango', () => {
    const data = {
      timpanometria: {
        oidoDerecho: {
          presion: -500,
        },
      },
      reflejosAcusticos: {},
    }

    const result = impedanceSchema.safeParse(data)
    expect(result.success).toBe(false)
  })

  it('debe rechazar compliance fuera de rango', () => {
    const data = {
      timpanometria: {
        oidoDerecho: {
          complianceMaxima: 15,
        },
      },
      reflejosAcusticos: {},
    }

    const result = impedanceSchema.safeParse(data)
    expect(result.success).toBe(false)
  })

  it('debe aceptar observaciones opcionales', () => {
    const data = {
      timpanometria: {
        oidoDerecho: {},
        oidoIzquierdo: {},
      },
      reflejosAcusticos: emptyReflejos,
      observaciones: 'Timpanograma tipo A bilateral',
    }

    const result = impedanceSchema.safeParse(data)
    expect(result.success).toBe(true)
  })
})
