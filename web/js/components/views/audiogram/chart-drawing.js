// js/components/views/audiogram/chart-drawing.js
// Funciones de dibujo: grid, datos, símbolos, panel de herramientas

Object.assign(AudiogramChartView.prototype, {

  drawGrid(freqs, xScale, yScale, plotW, plotH) {
    const ctx = this.ctx;
    const m = this.config.margin;

    // Líneas de grid
    ctx.strokeStyle = this.config.colors.grid;
    ctx.lineWidth = 1;

    // Líneas verticales (frecuencias)
    freqs.forEach((freq, i) => {
      const x = xScale(i);
      ctx.beginPath();
      ctx.moveTo(x, m.top);
      ctx.lineTo(x, m.top + plotH);
      ctx.stroke();
    });

    // Líneas horizontales (dB)
    for (let db = -10; db <= 120; db += 10) {
      const y = yScale(db);
      ctx.strokeStyle = db === 20 ? this.config.colors.gridStrong : this.config.colors.grid;
      ctx.lineWidth = db === 20 ? 2 : 1;
      ctx.beginPath();
      ctx.moveTo(m.left, y);
      ctx.lineTo(m.left + plotW, y);
      ctx.stroke();
    }

    // Etiquetas
    ctx.fillStyle = this.config.colors.text;
    ctx.font = '11px Arial';
    ctx.textAlign = 'center';

    // Frecuencias
    freqs.forEach((freq, i) => {
      const x = xScale(i);
      let label = freq;
      if (parseInt(freq) >= 1000) {
        label = (parseInt(freq) / 1000) + 'K';
      }
      ctx.fillText(label, x, m.top + plotH + 15);
    });

    // dB HL
    ctx.textAlign = 'right';
    for (let db = -10; db <= 120; db += 10) {
      const y = yScale(db);
      ctx.fillText(db.toString(), m.left - 5, y + 4);
    }
  },

  drawLDLLabel(data, xScale, yScale) {
    // Dibujar etiqueta "LDL" si hay datos
    const hasLDL = data.ldl_disconfort?.oido_derecho || data.ldl_disconfort?.oido_izquierdo;
    if (hasLDL) {
      this.ctx.fillStyle = this.config.colors.text;
      this.ctx.font = 'bold 10px Arial';
      this.ctx.textAlign = 'left';
      this.ctx.fillText('LDL', this.config.margin.left + 5, this.config.margin.top + 15);
    }
  },

  drawToolPanel() {
    const panelX = 10;
    const panelY = 10;
    const buttonSize = 30;
    const spacing = 5;

    const tools = [
      { id: 'aereo_od', label: 'AD', color: this.config.colors.od },
      { id: 'aereo_oi', label: 'AI', color: this.config.colors.oi },
      { id: 'oseo_od', label: 'OD', color: this.config.colors.od },
      { id: 'oseo_oi', label: 'OI', color: this.config.colors.oi },
      { id: 'ldl_od', label: 'LD', color: this.config.colors.od },
      { id: 'ldl_oi', label: 'LI', color: this.config.colors.oi },
      { id: 'fullscreen', label: '⛶', color: '#666' }
    ];

    const ctx = this.ctx;

    tools.forEach((tool, i) => {
      const x = panelX + i * (buttonSize + spacing);
      const y = panelY;

      // Fondo del botón
      ctx.fillStyle = this.activeTool === tool.id ?
      'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.8)';
      ctx.fillRect(x, y, buttonSize, buttonSize);

      // Borde del botón
      ctx.strokeStyle = tool.color;
      ctx.lineWidth = this.activeTool === tool.id ? 3 : 1;
      ctx.strokeRect(x, y, buttonSize, buttonSize);

      // Texto del botón
      ctx.fillStyle = tool.color;
      ctx.font = '10px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(tool.label, x + buttonSize/2, y + buttonSize/2 + 3);
    });
  },

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
        const stateKey = `${f}_${type}`;
        const symbolState = this.symbolStates[stateKey];

        // Solo renderizar si hay datos O estado interactivo
        if ((threshold === null || threshold === undefined || threshold === '') && !symbolState) return;

        let value;
        if (threshold !== null && threshold !== undefined && threshold !== '') {
          value = parseInt(threshold, 10);
        } else if (symbolState) {
          value = this.getSymbolDbFromState(stateKey) || 50;
        } else {
          return;
        }

        const x = xScale(i);
        let isMasked = false;
        let isAbsent = false;

        if (type.startsWith('ldl_')) {
          isAbsent = (value > 120 || threshold === 'ausente' || threshold === 'absent');
        } else {
          isMasked = masking[type] ? (masking[type][f] || false) : false;
        }

        // Determinar símbolo
        let symbol;
        const currentSymbolState = symbolState || 'normal';

        if (currentSymbolState === 'no_response') {
          symbol = type === 'aereo_od' ? 'no_response_circle' :
          type === 'aereo_oi' ? 'no_response_x' : st.unmasked;
        } else if (currentSymbolState === 'vt') {
          symbol = type === 'aereo_od' ? 'vt_circle' :
          type === 'aereo_oi' ? 'vt_x' : st.unmasked;
        } else if (currentSymbolState === 'masked') {
          symbol = st.masked;
        } else if (type.startsWith('ldl_')) {
          symbol = isAbsent ? st.masked : st.unmasked;
        } else {
          symbol = isMasked ? st.masked : st.unmasked;
        }

        // Usar la posición real del valor, sin forzar movimientos automáticos
        const y = yScale(value);
        let adjustedX = x;
        let adjustedY = y;

        // Ajustar coordenadas según el tipo
        if (type === 'oseo_od') {
          adjustedX = x - this.boneOffset;
        } else if (type === 'oseo_oi') {
          adjustedX = x + this.boneOffset;
        } else if (type.startsWith('ldl_')) {
          if (type === 'ldl_od') {
            adjustedX = x - this.ldlOffsetX;
          } else {
            adjustedX = x + this.ldlOffsetX;
          }
          adjustedY = y - this.ldlOffsetY;

          if (!isAbsent) {
            pts.push({ x: adjustedX, y: adjustedY });
          }
        } else {
          pts.push({ x: adjustedX, y: adjustedY });
        }

        if (type === 'oseo_od' || type === 'oseo_oi') {
          pts.push({ x: adjustedX, y: adjustedY });
        }

        // Dibujar el símbolo en su posición real
        // Para "no respuesta", usar símbolo de flecha si el valor es exactamente donde no hay respuesta
        // pero mantener la posición donde se hizo clic
        if (currentSymbolState === 'no_response') {
          // Dibujar el símbolo original (circle o x) en su posición real
          const baseSymbol = type === 'aereo_od' ? 'circle' : 'x';
          this.drawSymbol(adjustedX, adjustedY, baseSymbol, st.color);
          // Dibujar la flecha JUSTO debajo, sin mover el símbolo
          this.drawSymbol(adjustedX, adjustedY + this.symbolSize + 8, 'arrow', st.color);
        } else {
          this.drawSymbol(adjustedX, adjustedY, symbol, st.color);
        }
      });

      // Conectar líneas
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

});
