// js/components/views/audiogram-charts.js
class AudiogramChartView {
  constructor(canvasId) {
    this.canvasId = canvasId;
    this.canvas = null;
    this.ctx = null;

    // ========== CONFIGURACIÓN DE SÍMBOLOS Y TAMAÑOS ==========
    this.symbolSize = 6; // Radio/tamaño base de símbolos (configurable)
    this.boneOffset = 14; // Padding horizontal para símbolos óseos (configurable)
    this.ldlOffsetX = 8; // Desplazamiento horizontal LDL (configurable)
    this.ldlOffsetY = 8; // Desplazamiento vertical LDL (configurable)

    // Atenuación interaural por frecuencia (dB)
    this.interauralAttenuation = {
      125: 35,
      250: 40, 500: 40, 1000: 40,
      2000: 45, 3000: 45,
      4000: 50, 8000: 50
    };

    this.config = {
      margin: { top: 30, right: 40, bottom: 50, left: 60 },
      colors: {
        od: '#dc3545', // OD (rojo)
        oi: '#007bff', // OI (azul)
        grid: '#ddd',
        gridStrong: '#333',
        text: '#333'
      }
    };
  }

  init() {
    this.canvas = document.getElementById(this.canvasId);
    if (!this.canvas) return false;
    this.ctx = this.canvas.getContext('2d');
    return true;
  }

  render(data, opts = {}) {
    if (!this.init()) return;
    const ctx = this.ctx, cv = this.canvas;

    // limpiar
    ctx.clearRect(0, 0, cv.width, cv.height);

    // layout
    const m = this.config.margin;
    const plotW = cv.width  - m.left - m.right;
    const plotH = cv.height - m.top  - m.bottom;

    // frecuencias a mostrar
    const freqs = opts.freqs ??
    (opts.showHighFreq
    ? ['125','250','500','1000','2000','4000','8000','9000','10000','11200','12500','14000','16000','18000','20000']
    : ['125','250','500','1000','2000','4000','8000']);

    // escalas
    const xScale = (i) => m.left + (i / (freqs.length - 1)) * plotW;
    const yScale = (db) => m.top + ((db + 10) / 130) * plotH;

    // grilla y ejes
    this.drawGrid(freqs, xScale, yScale, plotW, plotH);

    //LDL label

    this.drawLDLLabel(data, xScale, yScale);


    // datos con enmascaramiento automático
    this.drawData(data, freqs, xScale, yScale);
  }

  drawGrid(freqs, xScale, yScale, plotW, plotH) {
    const ctx = this.ctx, m = this.config.margin;

    // verticales (frecuencias)
    ctx.strokeStyle = this.config.colors.grid;
    ctx.lineWidth = 1;
    ctx.fillStyle = '#666';
    ctx.font = '11px Arial';

    freqs.forEach((f, i) => {
      const x = xScale(i);
      ctx.beginPath();
      ctx.moveTo(x, m.top);
      ctx.lineTo(x, m.top + plotH);
      ctx.stroke();
    });

    // horizontales (dB) - línea gruesa en 20 dB
    for (let db = -10; db <= 120; db += 10) {
      if (db === 20) {
        ctx.strokeStyle = this.config.colors.gridStrong;
        ctx.lineWidth = 3; // Línea gruesa en 20 dB (límite normalidad)
      } else if (db === 0) {
        ctx.strokeStyle = this.config.colors.gridStrong;
        ctx.lineWidth = 2;
      } else {
        ctx.strokeStyle = this.config.colors.grid;
        ctx.lineWidth = 1;
      }
      const y = yScale(db);
      ctx.beginPath();
      ctx.moveTo(m.left, y);
      ctx.lineTo(m.left + plotW, y);
      ctx.stroke();

      if (db >= 0 && db <= 120) {

        ctx.fillStyle = '#333';
        ctx.fillText(String(db), m.left - 25, y + 3);
      }
    }

    // etiquetas superiores (frecuencias)
    ctx.fillStyle = '#333';
    ctx.font = '11px Arial';
    freqs.forEach((f, i) => {
      const x = xScale(i);
      ctx.save();
      ctx.translate(x, m.top - 10);
      ctx.rotate(-Math.PI/4);
      ctx.fillText(f, -10, 0);
      ctx.restore();
    });

    // títulos
    ctx.fillStyle = '#333';
    ctx.font = 'bold 12px Arial';
    ctx.fillText('Frecuencia (Hz)', m.left + plotW/2 - 40, m.top + plotH + 40);

    ctx.save();
    ctx.translate(15, m.top + plotH/2);
    ctx.rotate(-Math.PI/2);
    ctx.fillText('Umbral (dB HL)', -40, 0);
    ctx.restore();
  }

  // ========== LÓGICA DE ENMASCARAMIENTO AUTOMÁTICO ==========
  calculateMasking(data, freqs) {
    const masking = {
      aereo_od: {}, aereo_oi: {},
      oseo_od: {}, oseo_oi: {}
    };

    freqs.forEach(f => {
      const freq = parseInt(f);
      const ai = this.getInterauralAttenuation(freq);

      // Obtener umbrales
      const va_od = this.getThreshold(data, 'aereo_od', f);
      const va_oi = this.getThreshold(data, 'aereo_oi', f);
      const vo_od = this.getThreshold(data, 'oseo_od', f) ?? va_od; // Si no hay ósea, asumir = aérea
      const vo_oi = this.getThreshold(data, 'oseo_oi', f) ?? va_oi;

      // === ENMASCARAMIENTO VÍA AÉREA ===
      // Solo se enmascara el oído PEOR (más dB), no el mejor
      if (va_od !== null && va_oi !== null) {
        const diferencia = Math.abs(va_od - va_oi);
        if (diferencia >= ai) {
          // Enmascarar solo el oído con PEOR umbral (más dB)
          if (va_od > va_oi) {
            masking.aereo_od[f] = true; // OD es peor, se enmascara
          } else {
            masking.aereo_oi[f] = true; // OI es peor, se enmascara
          }
        }
      }

      // === ENMASCARAMIENTO VÍA ÓSEA ===
      if (vo_od !== null && va_od !== null) {
        masking.oseo_od[f] = this.needsBoneMasking(va_od, vo_od, vo_oi);
      }
      if (vo_oi !== null && va_oi !== null) {
        masking.oseo_oi[f] = this.needsBoneMasking(va_oi, vo_oi, vo_od);
      }
    });

    return masking;
  }

  needsBoneMasking(va_same, vo_same, vo_contra) {
    // Regla 1: Gap aéreo-óseo ≥ 10 dB en el mismo oído
    if ((va_same - vo_same) >= 10) return true;

    // Regla 2: VO contralateral mejor que VO del oído en estudio (AI = 0 dB)
    if (vo_contra !== null && vo_contra < vo_same) return true;

    return false;
  }

  getInterauralAttenuation(freq) {
    // Buscar la frecuencia más cercana en la tabla de AI
    const availableFreqs = Object.keys(this.interauralAttenuation).map(f => parseInt(f));
    const closest = availableFreqs.reduce((prev, curr) =>
    Math.abs(curr - freq) < Math.abs(prev - freq) ? curr : prev
    );
    return this.interauralAttenuation[closest];
  }


  // Agregar etiqueta "LDL:" si hay datos de LDL
  drawLDLLabel(data, xScale, yScale) {
    // Verificar si hay datos de LDL
    const hasLDLData = data.ldl_disconfort &&
    (Object.keys(data.ldl_disconfort.oido_derecho || {}).length > 0 ||
    Object.keys(data.ldl_disconfort.oido_izquierdo || {}).length > 0);

    if (!hasLDLData) return;

    const ctx = this.ctx;

    // Posición: entre 100-120 dB (Y) y entre 125-250 Hz (X)
    // Usar el punto medio de cada rango
    const labelY = yScale(95); // Punto medio entre 100-120

    // Para X, encontrar posición entre 125 Hz (índice 0) y 250 Hz (índice 1)
    const labelX = (xScale(0) + xScale(1)) / 2; // Punto medio entre índices 0 y 1

    // Configurar estilo del texto
    ctx.save();
    ctx.fillStyle = this.config.colors.text;
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Dibujar texto "LDL:"
    ctx.fillText('LDL:', labelX, labelY);

    // Dibujar subrayado
    const textWidth = ctx.measureText('LDL:').width;
    ctx.strokeStyle = this.config.colors.text;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(labelX - textWidth/2, labelY + 8);
    ctx.lineTo(labelX + textWidth/2, labelY + 8);
    ctx.stroke();

    ctx.restore();
  }

  // ========== DIBUJO DE DATOS ==========
  drawData(data, freqs, xScale, yScale) {
    const masking = this.calculateMasking(data, freqs);

    const styles = {
      aereo_od: { color: this.config.colors.od, unmasked: 'circle', masked: 'triangle', line: 'solid' },
      aereo_oi: { color: this.config.colors.oi, unmasked: 'x', masked: 'square', line: 'solid' },
      oseo_od:  { color: this.config.colors.od, unmasked: 'bone_left', masked: 'bone_bracket_left', line: 'dashed' },
      oseo_oi:  { color: this.config.colors.oi, unmasked: 'bone_right', masked: 'bone_bracket_right', line: 'dashed' },
      ldl_od:   { color: this.config.colors.od, unmasked: 'ldl_present', masked: 'ldl_absent', line: 'solid' },
      ldl_oi:   { color: this.config.colors.oi, unmasked: 'ldl_present', masked: 'ldl_absent', line: 'solid' }
    };

    Object.keys(styles).forEach(type => {
      const st = styles[type];
      const pts = [];

      freqs.forEach((f, i) => {
        const threshold = this.getThreshold(data, type, f);
        if (threshold === null || threshold === undefined || threshold === '') return;

        const value = parseInt(threshold, 10);
        const x = xScale(i);

        // Determinar si LDL es ausente (valor especial o >120)
        let isMasked = false;
        let isAbsent = false;

        if (type.startsWith('ldl_')) {
          isAbsent = (value > 120 || threshold === 'ausente' || threshold === 'absent');
        } else {
          isMasked = masking[type] ? (masking[type][f] || false) : false;
        }

        const symbol = (type.startsWith('ldl_')) ?
        (isAbsent ? st.masked : st.unmasked) :
        (isMasked ? st.masked : st.unmasked);

        if (value === 130) {
          // Símbolo de flecha hacia abajo (no response)
          const y = yScale(120);
          this.drawSymbol(x, y, 'arrow', st.color);
        } else {
          const y = yScale(value);
          let adjustedX = x;
          let adjustedY = y;

          // Ajustar coordenadas según tipo de símbolo
          if (type === 'oseo_od') {
            adjustedX = x - this.boneOffset; // < y [
          } else if (type === 'oseo_oi') {
            adjustedX = x + this.boneOffset; // > y ]
          } else if (type.startsWith('ldl_')) {
            // LDL tienen offset tanto en X como en Y
            if (type === 'ldl_od') {
              adjustedX = x - this.ldlOffsetX;
            } else {
              adjustedX = x + this.ldlOffsetX;
            }
            adjustedY = y - this.ldlOffsetY;

            // Solo agregar a puntos si NO es ausente (para conectar líneas)
            if (!isAbsent) {
              pts.push({ x: adjustedX, y: adjustedY });
            }
          } else {
            // Aéreos sin offset
            pts.push({ x: adjustedX, y: adjustedY });
          }

          // Para óseos, agregar puntos ajustados
          if (type === 'oseo_od' || type === 'oseo_oi') {
            pts.push({ x: adjustedX, y: adjustedY });
          }

          this.drawSymbol(x, y, symbol, st.color);
        }
      });

      // Conectar puntos con líneas
      if (pts.length > 1 && st.line !== 'none') {
        const ctx = this.ctx;
        ctx.strokeStyle = st.color;
        ctx.lineWidth = 2;
        ctx.setLineDash(st.line === 'dashed' ? [4,4] : []);
        ctx.beginPath();
        ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    });
  }

  getThreshold(data, type, freq) {
    switch (type) {
      case 'aereo_od': return data.umbrales_aereos?.oido_derecho?.[freq];
      case 'aereo_oi': return data.umbrales_aereos?.oido_izquierdo?.[freq];
      case 'oseo_od':  return data.umbrales_oseos?.oido_derecho?.[freq];
      case 'oseo_oi':  return data.umbrales_oseos?.oido_izquierdo?.[freq];
      case 'ldl_od':   return data.ldl_disconfort?.oido_derecho?.[freq];
      case 'ldl_oi':   return data.ldl_disconfort?.oido_izquierdo?.[freq];
      default: return null;
    }
  }

  // ========== SÍMBOLOS AUDIOLÓGICOS ESTÁNDAR ==========
  drawSymbol(x, y, symbol, color) {
    const ctx = this.ctx;
    const size = this.symbolSize;
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 2;

    switch (symbol) {
      case 'circle': // O - Aérea OD sin masking
        ctx.beginPath();
        ctx.arc(x, y, size, 0, 2 * Math.PI);
        ctx.stroke();
        break;

      case 'x': // X - Aérea OI sin masking
        ctx.beginPath();
        ctx.moveTo(x - size, y - size);
        ctx.lineTo(x + size, y + size);
        ctx.moveTo(x + size, y - size);
        ctx.lineTo(x - size, y + size);
        ctx.stroke();
        break;

      case 'square': // Cuadrado - Aérea OI con masking
        ctx.beginPath();
        ctx.rect(x - size, y - size, size * 2, size * 2);
        ctx.stroke();
        break;

      case 'triangle': // Triángulo - Aérea OD con masking
        ctx.beginPath();
        ctx.moveTo(x, y - size);
        ctx.lineTo(x - size, y + size);
        ctx.lineTo(x + size, y + size);
        ctx.closePath();
        ctx.stroke();
        break;

      case 'bone_left': // < - Ósea OD sin masking
        ctx.beginPath();
        ctx.moveTo(x - this.boneOffset + size, y - size); // línea superior
        ctx.lineTo(x - this.boneOffset - size, y);
        ctx.moveTo(x - this.boneOffset - size, y);       // línea inferior
        ctx.lineTo(x - this.boneOffset + size, y + size);
        ctx.stroke();
        break;

      case 'bone_right': // > - Ósea OI sin masking
        ctx.beginPath();
        ctx.moveTo(x + this.boneOffset - size, y - size); // línea superior
        ctx.lineTo(x + this.boneOffset + size, y);
        ctx.moveTo(x + this.boneOffset + size, y);       // línea inferior
        ctx.lineTo(x + this.boneOffset - size, y + size);
        ctx.stroke();
        break;

      case 'bone_bracket_left': // [ - Ósea OD con masking
        const leftX = x - this.boneOffset;
        ctx.beginPath();
        ctx.moveTo(leftX - size, y - size);
        ctx.lineTo(leftX - size/2, y - size);
        ctx.moveTo(leftX - size, y - size);
        ctx.lineTo(leftX - size, y + size);
        ctx.moveTo(leftX - size, y + size);
        ctx.lineTo(leftX - size/2, y + size);
        ctx.stroke();
        break;

      case 'bone_bracket_right': // ] - Ósea OI con masking
        const rightX = x + this.boneOffset;
        ctx.beginPath();
        ctx.moveTo(rightX + size, y - size);
        ctx.lineTo(rightX + size/2, y - size);
        ctx.moveTo(rightX + size, y - size);
        ctx.lineTo(rightX + size, y + size);
        ctx.moveTo(rightX + size, y + size);
        ctx.lineTo(rightX + size/2, y + size);
        ctx.stroke();
        break;

      case 'ldl_present': // Triángulo rectángulo vacío - LDL presente
        const ldlX = (color === this.config.colors.od) ?
        x - this.ldlOffsetX : x + this.ldlOffsetX;
        const ldlY = y - this.ldlOffsetY;

        ctx.beginPath();
        if (color === this.config.colors.od) {
          // OD: cateto adyacente abajo, cateto opuesto hacia centro (derecha), hipotenusa arriba
          ctx.moveTo(ldlX - size, ldlY + size); // esquina inferior izq (cateto adyacente)
          ctx.lineTo(ldlX + size, ldlY + size); // esquina inferior der (cateto adyacente)
          ctx.lineTo(ldlX + size, ldlY - size); // esquina superior der (cateto opuesto hacia centro)
        } else {
          // OI: cateto adyacente abajo, cateto opuesto hacia centro (izquierda), hipotenusa arriba
          ctx.moveTo(ldlX + size, ldlY + size); // esquina inferior der (cateto adyacente)
          ctx.lineTo(ldlX - size, ldlY + size); // esquina inferior izq (cateto adyacente)
          ctx.lineTo(ldlX - size, ldlY - size); // esquina superior izq (cateto opuesto hacia centro)
        }
        ctx.closePath();
        ctx.stroke();
        break;

      case 'ldl_absent': // Triángulo rectángulo + flecha - LDL ausente
        const absentX = (color === this.config.colors.od) ?
        x - this.ldlOffsetX : x + this.ldlOffsetX;
        const absentY = y - this.ldlOffsetY;

        // Dibujar triángulo rectángulo con orientación correcta
        ctx.beginPath();
        if (color === this.config.colors.od) {
          ctx.moveTo(absentX - size, absentY + size); // cateto adyacente abajo
          ctx.lineTo(absentX + size, absentY + size);
          ctx.lineTo(absentX + size, absentY - size); // cateto opuesto hacia centro
        } else {
          ctx.moveTo(absentX + size, absentY + size); // cateto adyacente abajo
          ctx.lineTo(absentX - size, absentY + size);
          ctx.lineTo(absentX - size, absentY - size); // cateto opuesto hacia centro
        }
        ctx.closePath();
        ctx.stroke();

        // Línea vertical desde el cateto opuesto hacia abajo
        const lineStartX = (color === this.config.colors.od) ?
        absentX + size : absentX - size;
        const lineEndY = absentY + size * 2;

        ctx.beginPath();
        ctx.moveTo(lineStartX, absentY + size);
        ctx.lineTo(lineStartX, lineEndY);
        ctx.stroke();

        // Flecha al final
        ctx.beginPath();
        ctx.moveTo(lineStartX - size/2, lineEndY - size/2);
        ctx.lineTo(lineStartX, lineEndY);
        ctx.lineTo(lineStartX + size/2, lineEndY - size/2);
        ctx.stroke();
        break;

      case 'arrow': // Flecha hacia abajo - No response
        ctx.beginPath();
        ctx.moveTo(x, y - size * 1.5);
        ctx.lineTo(x, y + size * 1.5);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x - size, y + size);
        ctx.lineTo(x, y + size * 1.5);
        ctx.lineTo(x + size, y + size);
        ctx.stroke();
        break;
    }
  }
}

window.AudiogramChartView = AudiogramChartView;
