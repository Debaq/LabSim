import { describe, it, expect, beforeEach } from 'vitest'
import { usePatientStore } from '../patient-store'

describe('usePatientStore', () => {
  beforeEach(() => {
    // Resetear el store antes de cada test
    usePatientStore.getState().resetData()
  })

  describe('updateModule', () => {
    it('debe actualizar los datos de un módulo específico', () => {
      const audiometryData = { umbralesAereos: { oidoDerecho: { '1000': 25 } } }

      usePatientStore.getState().updateModule('audiometry', audiometryData)

      const state = usePatientStore.getState()
      expect(state.data.audiometry).toEqual(audiometryData)
    })

    it('debe actualizar patientInfo sin afectar otros módulos', () => {
      const patientInfo = { firstName: 'Juan', lastName: 'Pérez' }
      const impedanceData = { timpanometria: { oidoDerecho: {} } }

      usePatientStore.getState().updateModule('patientInfo', patientInfo)
      usePatientStore.getState().updateModule('impedance', impedanceData)

      const state = usePatientStore.getState()
      expect(state.data.patientInfo).toEqual(patientInfo)
      expect(state.data.impedance).toEqual(impedanceData)
      expect(state.data.anamnesis).toEqual({})
    })

    it('debe sobreescribir datos previos del módulo', () => {
      usePatientStore.getState().updateModule('anamnesis', { motivo: 'primera consulta' })
      usePatientStore.getState().updateModule('anamnesis', { motivo: 'control' })

      const state = usePatientStore.getState()
      expect(state.data.anamnesis).toEqual({ motivo: 'control' })
    })
  })

  describe('resetData', () => {
    it('debe limpiar todos los módulos a objetos vacíos', () => {
      usePatientStore.getState().updateModule('audiometry', { threshold: 25 })
      usePatientStore.getState().setPatientId('patient-123')

      usePatientStore.getState().resetData()

      const state = usePatientStore.getState()
      expect(state.data.audiometry).toEqual({})
      expect(state.data.patientInfo).toEqual({})
      expect(state.data.impedance).toEqual({})
      expect(state.currentPatientId).toBeNull()
    })

    it('debe resetear el patientId a null', () => {
      usePatientStore.getState().setPatientId('abc-123')
      usePatientStore.getState().resetData()

      expect(usePatientStore.getState().currentPatientId).toBeNull()
    })
  })

  describe('setPatientId', () => {
    it('debe establecer un ID de paciente', () => {
      usePatientStore.getState().setPatientId('patient-456')

      expect(usePatientStore.getState().currentPatientId).toBe('patient-456')
    })

    it('debe poder establecer el ID a null', () => {
      usePatientStore.getState().setPatientId('patient-789')
      usePatientStore.getState().setPatientId(null)

      expect(usePatientStore.getState().currentPatientId).toBeNull()
    })

    it('debe mantener los datos al cambiar el ID', () => {
      usePatientStore.getState().updateModule('audiometry', { test: true })
      usePatientStore.getState().setPatientId('new-patient')

      const state = usePatientStore.getState()
      expect(state.currentPatientId).toBe('new-patient')
      expect(state.data.audiometry).toEqual({ test: true })
    })
  })
})
