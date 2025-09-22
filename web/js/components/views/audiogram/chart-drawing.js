// js/components/views/audiogram/chart-drawing.js
// Funciones de dibujo: grilla, etiquetas, panel de herramientas, datos

Object.assign(AudiogramChartView.prototype, {

  drawGrid(freqs, xScale, yScale, plotW, plotH) {
    const ctx = this.ctx, m = this.config.margin;

    // Líneas verticales (frecuencias)
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

    // Líneas horizontales (dB)
    for (let db = -10; db <= 120; db += 10) {
      if (db === 20) {
        ctx.strokeStyle = this.config.colors.gridStrong;
        ctx.lineWidth = 3; // Línea gruesa en 20 dB
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

    // Etiquetas superiores (frecuencias)
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

    // Títulos de ejes
    ctx.fillStyle = '#333';
    ctx.font = 'bold 12px Arial';
    ctx.fillText('Frecuencia (Hz)', m.left + plotW/2 - 40, m.top + plotH + 40);

    ctx.save();
    ctx.translate(15, m.top + plotH/2);
    ctx.rotate(-Math.PI/2);
    ctx.fillText('Umbral (dB HL)', -40, 0);
    ctx.restore();
  },

  drawLDLLabel(data, xScale, yScale) {
    const hasLDLData = data.ldl_disconfort &&
      (Object.keys(data.ldl_disconfort.oido_derecho || {}).length > 0 ||
       Object.keys(data.ldl_disconfort.oido_izquierdo || {}).length > 0);

    if (!hasLDLData) return;

    const ctx = this.ctx;
    const labelY = yScale(95);
    const labelX = (xScale(0) + xScale(1)) / 2;

    ctx.save();
    ctx.fillStyle = this.config.colors.text;
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('LDL:', labelX, labelY);

    const textWidth = ctx.measureText('LDL:').width;
    ctx.strokeStyle = this.config.colors.text;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(labelX - textWidth/2, labelY + 8);
    ctx.lineTo(labelX + textWidth/2, labelY + 8);
    ctx.stroke();
    ctx.restore();
  },

  drawToolPanel() {
    if (!this.isInteractive) return;

    const ctx = this.ctx;
    const panelX = 10;
    const panelY = 10;
    const buttonSize = 30;
    const spacing = 5;

    const tools = [
      { id: 'aereo_od', label: 'O', color: this.config.colors.od },
      { id: 'aereo_oi', label: 'X', color: this.config.colors.oi },
      { id: 'oseo_od', label: '<', color: this.config.colors.od },
      { id: 'oseo_oi', label: '>', color: this.config.colors.oi },
      { id: 'ldl_od', label: 'LDL-OD', color: this.config.colors.od },
      { id: 'ldl_oi', label: 'LDL-OI', color: this.config.colors.oi },
      { id: 'fullscreen', label: '⛶', color: '#333' }
    ];

    tools.forEach((tool, i) => {
      const x = panelX + i * (buttonSize + spacing);
      const y = panelY;

      // Fondo del botón
      ctx.fillStyle = this.activeTool === tool.id ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.8)';
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

        if (value === 130) {
          const y = yScale(120);
          this.drawSymbol(x, y, 'arrow', st.color);
        } else {
          const y = yScale(value);
          let adjustedX = x;
          let adjustedY = y;

          // Ajustar coordenadas
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

          this.drawSymbol(x, y, symbol, st.color);
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