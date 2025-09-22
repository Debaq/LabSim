// js/components/views/audiogram/chart-interaction.js
// Funciones de interacción: clicks, herramientas, estados, pantalla completa

Object.assign(AudiogramChartView.prototype, {

  handleCanvasClick(event) {
    if (!this.isInteractive) return;

    const rect = this.canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;

    // Verificar click en panel de herramientas
    if (this.handleToolPanelClick(mouseX, mouseY)) return;

    // Verificar click en símbolo existente para cambiar estado
    const symbolClick = this.findClickedSymbol(mouseX, mouseY);
    if (symbolClick) {
      this.handleSymbolStateChange(symbolClick);
      return;
    }

    // Verificar click en intersección del grid
    const intersection = this.findNearestIntersection(mouseX, mouseY);
    if (intersection) {
      this.handleIntersectionClick(intersection);
    }
  },

  handleToolPanelClick(mouseX, mouseY) {
    const panelX = 10;
    const panelY = 10;
    const buttonSize = 30;
    const spacing = 5;

    const tools = ['aereo_od', 'aereo_oi', 'oseo_od', 'oseo_oi', 'ldl_od', 'ldl_oi', 'fullscreen'];

    for (let i = 0; i < tools.length; i++) {
      const x = panelX + i * (buttonSize + spacing);
      const y = panelY;

      if (mouseX >= x && mouseX <= x + buttonSize && mouseY >= y && mouseY <= y + buttonSize) {
        if (tools[i] === 'fullscreen') {
          this.toggleFullscreen();
        } else {
          this.activeTool = tools[i];
          this.render(this.lastData, this.lastOpts);
        }
        return true;
      }
    }
    return false;
  },

  findClickedSymbol(mouseX, mouseY) {
    if (!this.lastOpts || !this.lastOpts.freqs) return null;

    const m = this.config.margin;
    const plotW = this.canvas.width - m.left - m.right;
    const plotH = this.canvas.height - m.top - m.bottom;
    const freqs = this.lastOpts.freqs;

    const xScale = (i) => m.left + (i / (freqs.length - 1)) * plotW;
    const yScale = (db) => m.top + ((db + 10) / 130) * plotH;

    // Radio pequeño para clic preciso en símbolo
    const clickRadius = 8;

    for (let freqIndex = 0; freqIndex < freqs.length; freqIndex++) {
      const freq = freqs[freqIndex];
      const stateKey = `${freq}_${this.activeTool}`;

      // Solo verificar si existe un símbolo en esta posición
      if (this.symbolStates[stateKey] || this.getThreshold(this.lastData, this.activeTool, freq)) {
        let symbolDb;

        // Obtener la posición actual del símbolo
        if (this.symbolStatesDb[stateKey]) {
          symbolDb = this.symbolStatesDb[stateKey];
        } else {
          const threshold = this.getThreshold(this.lastData, this.activeTool, freq);
          if (threshold !== null && threshold !== undefined && threshold !== '') {
            symbolDb = parseInt(threshold, 10);
          } else {
            continue;
          }
        }

        const symbolX = xScale(freqIndex);
        const symbolY = yScale(symbolDb);

        // Ajustar coordenadas según el tipo de símbolo
        let adjustedX = symbolX;
        if (this.activeTool === 'oseo_od') {
          adjustedX = symbolX - this.boneOffset;
        } else if (this.activeTool === 'oseo_oi') {
          adjustedX = symbolX + this.boneOffset;
        } else if (this.activeTool.startsWith('ldl_')) {
          if (this.activeTool === 'ldl_od') {
            adjustedX = symbolX - this.ldlOffsetX;
          } else {
            adjustedX = symbolX + this.ldlOffsetX;
          }
        }

        const distance = Math.sqrt(Math.pow(mouseX - adjustedX, 2) + Math.pow(mouseY - symbolY, 2));

        if (distance <= clickRadius) {
          return {
            freq: freq,
            freqIndex: freqIndex,
            currentDb: symbolDb,
            stateKey: stateKey
          };
        }
      }
    }

    return null;
  },

  handleSymbolStateChange(symbolClick) {
    const { freq, stateKey, currentDb } = symbolClick;

    // Obtener estado actual
    const currentState = this.symbolStates[stateKey] || 'normal';

    // Ciclar al siguiente estado SIN cambiar la posición
    const nextState = this.getNextState(currentState, freq);

    if (nextState === 'empty') {
      delete this.symbolStates[stateKey];
      delete this.symbolStatesDb[stateKey];
      // Actualizar datos para eliminar el umbral
      this.updateAudiogramData(freq, this.activeTool, null, 'empty');
    } else {
      this.symbolStates[stateKey] = nextState;
      // MANTENER la posición actual, no cambiarla
      this.symbolStatesDb[stateKey] = currentDb;
      // Actualizar datos manteniendo la intensidad actual
      this.updateAudiogramData(freq, this.activeTool, currentDb, nextState);
    }

    this.render(this.lastData, this.lastOpts);
  },

  findNearestIntersection(mouseX, mouseY) {
    if (!this.lastOpts || !this.lastOpts.freqs) return null;

    const m = this.config.margin;
    const plotW = this.canvas.width - m.left - m.right;
    const plotH = this.canvas.height - m.top - m.bottom;
    const freqs = this.lastOpts.freqs;

    const xScale = (i) => m.left + (i / (freqs.length - 1)) * plotW;
    const yScale = (db) => m.top + ((db + 10) / 130) * plotH;

    // Verificar que esté dentro del área del plot
    if (mouseX < m.left || mouseX > m.left + plotW ||
      mouseY < m.top || mouseY > m.top + plotH) {
      return null;
      }

      let closestIntersection = null;
    let minDistance = 12; // Radio de precisión para intersecciones

    freqs.forEach((freq, freqIndex) => {
      for (let db = -10; db <= 120; db += 5) {
        const x = xScale(freqIndex);
        const y = yScale(db);

        const distance = Math.sqrt(Math.pow(mouseX - x, 2) + Math.pow(mouseY - y, 2));

        if (distance < minDistance) {
          minDistance = distance;
          closestIntersection = {
            freq: freq,
            db: db,
            x: x,
            y: y,
            freqIndex: freqIndex
          };
        }
      }
    });

    return closestIntersection;
  },

  handleIntersectionClick(intersection) {
    const { freq, db } = intersection;
    const stateKey = `${freq}_${this.activeTool}`;

    // Verificar si ya existe un umbral (de datos o interactivo)
    const hasExistingThreshold = this.symbolStates[stateKey] ||
    this.getThreshold(this.lastData, this.activeTool, freq);

    if (hasExistingThreshold) {
      // Si existe un umbral, MOVER a la nueva intensidad
      const currentState = this.symbolStates[stateKey] || 'normal';

      this.symbolStates[stateKey] = currentState;
      this.symbolStatesDb[stateKey] = db;

      // Actualizar datos con la nueva intensidad
      this.updateAudiogramData(freq, this.activeTool, db, currentState);
    } else {
      // Si NO existe umbral, CREAR nuevo símbolo
      const initialState = this.getInitialState(freq, this.activeTool, db, this.lastData);

      this.symbolStates[stateKey] = initialState;
      this.symbolStatesDb[stateKey] = db;

      // Actualizar datos con nuevo umbral
      this.updateAudiogramData(freq, this.activeTool, db, initialState);
    }

    this.render(this.lastData, this.lastOpts);
  },

  getNextState(currentState, freq) {
    const freq_num = parseInt(freq);
    const hasVT = freq_num === 125 || freq_num === 250;

    switch (currentState) {
      case 'normal':
        return 'masked';
      case 'masked':
        return 'no_response';
      case 'no_response':
        return hasVT ? 'vt' : 'empty';
      case 'vt':
        return 'empty';
      default:
        return 'normal';
    }
  },

  getInitialState(freq, toolType, db, data) {
    // Si necesita masking según reglas, empezar enmascarado
    const masking = this.calculateMasking(data, [freq]);
    if (masking[toolType] && masking[toolType][freq]) {
      return 'masked';
    }
    return 'normal';
  },

  // ========== PANTALLA COMPLETA ==========

  toggleFullscreen() {
    if (!this.isFullscreen) {
      this.canvas.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  },

  handleFullscreenChange() {
    this.isFullscreen = !!document.fullscreenElement;
    if (this.isFullscreen) {
      this.resizeForFullscreen();
    }
    this.render(this.lastData, this.lastOpts);
  },

  resizeForFullscreen() {
    if (this.isFullscreen) {
      this.canvas.width = window.innerWidth;
      this.canvas.height = window.innerHeight;
    }
  }

});
