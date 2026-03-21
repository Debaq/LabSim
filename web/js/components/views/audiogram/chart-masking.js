// js/components/views/audiogram/chart-masking.js
// Lógica de enmascaramiento automático según normas audiológicas

Object.assign(AudiogramChartView.prototype, {

  calculateMasking(data, freqs) {
    const masking = {
      aereo_od: {}, 
      aereo_oi: {},
      oseo_od: {}, 
      oseo_oi: {}
    };

    freqs.forEach(f => {
      const freq = parseInt(f);
      const ai = this.getInterauralAttenuation(freq);

      // Obtener umbrales
      const va_od = this.getThreshold(data, 'aereo_od', f);
      const va_oi = this.getThreshold(data, 'aereo_oi', f);
      const vo_od = this.getThreshold(data, 'oseo_od', f) ?? va_od;
      const vo_oi = this.getThreshold(data, 'oseo_oi', f) ?? va_oi;

      // ========== ENMASCARAMIENTO VÍA AÉREA ==========
      
      // Regla 1: Diferencia VA entre oídos ≥ AI
      if (va_od !== null && va_oi !== null) {
        const diferencia = Math.abs(va_od - va_oi);
        if (diferencia >= ai) {
          // Enmascarar el oído con PEOR umbral (mayor dB)
          if (va_od > va_oi) {
            masking.aereo_od[f] = true; // OD es peor
          } else {
            masking.aereo_oi[f] = true; // OI es peor
          }
        }
      }

      // Regla 2: VO contralateral mejor que VA del oído estudiado ≥ AI
      // Para OD: VA_OD - VO_OI ≥ AI
      if (va_od !== null && vo_oi !== null) {
        if ((va_od - vo_oi) >= ai) {
          masking.aereo_od[f] = true;
        }
      }

      // Para OI: VA_OI - VO_OD ≥ AI
      if (va_oi !== null && vo_od !== null) {
        if ((va_oi - vo_od) >= ai) {
          masking.aereo_oi[f] = true;
        }
      }

      // ========== ENMASCARAMIENTO VÍA ÓSEA ==========
      
      if (vo_od !== null && va_od !== null) {
        masking.oseo_od[f] = this.needsBoneMasking(va_od, vo_od, vo_oi, va_oi);
      }
      
      if (vo_oi !== null && va_oi !== null) {
        masking.oseo_oi[f] = this.needsBoneMasking(va_oi, vo_oi, vo_od, va_od);
      }
    });

    return masking;
  },

  needsBoneMasking(va_same, vo_same, vo_contra, va_contra) {
    // Regla 1: Gap aéreo-óseo ≥ 10 dB en el mismo oído
    if ((va_same - vo_same) >= 10) return true;

    // Regla 2: VO contralateral mejor que VO del oído estudiado ≥ 10 dB
    if (vo_contra !== null && (vo_same - vo_contra) >= 10) return true;

    // Regla 3: VA contralateral mejor que VO del oído estudiado ≥ 10 dB
    if (va_contra !== null && (vo_same - va_contra) >= 10) return true;

    return false;
  },

  getInterauralAttenuation(freq) {
    // Tabla de atenuación interaural por frecuencia (dB)
    // Basada en normas audiológicas internacionales
    const availableFreqs = Object.keys(this.interauralAttenuation).map(f => parseInt(f));
    
    // Buscar la frecuencia más cercana
    const closest = availableFreqs.reduce((prev, curr) =>
      Math.abs(curr - freq) < Math.abs(prev - freq) ? curr : prev
    );
    
    return this.interauralAttenuation[closest];
  }

});