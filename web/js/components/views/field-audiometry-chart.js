/**
 * FieldAudiometryChartView - Vista de Audiometría de Campo Libre
 * Audiograma con umbrales sin audífonos, con audífonos y ganancia funcional
 */

class FieldAudiometryChartView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.canvas = null;
        this.ctx = null;
        this.config = {
            margin: { top: 40, right: 50, bottom: 60, left: 70 },
            colors: {
                od_sin: '#dc3545',        // OD sin audífonos
                oi_sin: '#007bff',        // OI sin audífonos
                od_con: '#ff6b6b',        // OD con audífonos (más claro)
                oi_con: '#4dabf7',        // OI con audífonos (más claro)
                ganancia: '#28a745',      // Líneas de ganancia
                grid: '#e0e0e0',
                gridMajor: '#ccc',
                text: '#333',
                normalArea: 'rgba(40, 167, 69, 0.05)',
                threshold20: '#ffc107'
            }
        };

        // Frecuencias para audiometría de campo libre
        this.frequencies = [250, 500, 1000, 2000, 4000, 8000];
        
        // Símbolos para diferentes condiciones
        this.symbols = {
            sin_od: 'circle_open',     // ○ Círculo abierto rojo
            sin_oi: 'x',               // × X azul
            con_od: 'circle_filled',   // ● Círculo relleno rojo
            con_oi: 'triangle'         // ▲ Triángulo azul
        };

        // Líneas de conexión
        this.lineStyles = {
            sin_audifonos: { dash: [], width: 2 },      // Línea sólida
            con_audifonos: { dash: [8, 4], width: 2 }   // Línea punteada
        };
    }

    /**
     * Inicializar el canvas
     */
    init() {
        this.canvas = document.getElementById(this.canvasId);
        if (!this.canvas) {
            console.warn(`Canvas ${this.canvasId} no encontrado`);
            return false;
        }
        this.ctx = this.canvas.getContext('2d');
        return true;
    }

    /**
     * Renderizar audiograma de campo libre
     */
    render(data) {
        if (!this.init()) return;

        // Limpiar canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Configuración del área de dibujo
        const plotWidth = this.canvas.width - this.config.margin.left - this.config.margin.right;
        const plotHeight = this.canvas.height - this.config.margin.top - this.config.margin.bottom;

        // Funciones de escala
        const xScale = (freqIndex) => this.config.margin.left + (freqIndex / (this.frequencies.length - 1)) * plotWidth;
        const yScale = (threshold) => this.config.margin.top + (threshold / 120) * plotHeight; // 0-120 dB HL

        // Dibujar componentes
        this.drawGrid(plotWidth, plotHeight, xScale, yScale);
        this.drawNormalArea(xScale, yScale);
        this.drawAxes(plotWidth, plotHeight);
        this.drawAudiogramData(data, xScale, yScale);
        this.drawGananciaFuncional(data, xScale, yScale);
        this.drawLegend(data);
        this.drawFieldAudioInfo(data);
    }

    /**
     * Dibujar grilla del audiograma
     */
    drawGrid(width, height, xScale, yScale) {
        this.ctx.strokeStyle = this.config.colors.grid;
        this.ctx.lineWidth = 1;

        // Líneas verticales (frecuencias)
        this.frequencies.forEach((freq, index) => {
            const x = xScale(index);
            
            // Líneas más gruesas para frecuencias importantes (500, 1k, 2k, 4k)
            if ([500, 1000, 2000, 4000].includes(freq)) {
                this.ctx.strokeStyle = this.config.colors.gridMajor;
                this.ctx.lineWidth = 1.5;
            } else {
                this.ctx.strokeStyle = this.config.colors.grid;
                this.ctx.lineWidth = 1;
            }
            
            this.ctx.beginPath();
            this.ctx.moveTo(x, this.config.margin.top);
            this.ctx.lineTo(x, this.config.margin.top + height);
            this.ctx.stroke();
        });

        // Líneas horizontales (umbrales - cada 10 dB)
        for (let threshold = 0; threshold <= 120; threshold += 10) {
            const y = yScale(threshold);
            
            // Línea más gruesa en 20 dB (límite normalidad)
            if (threshold === 20) {
                this.ctx.strokeStyle = this.config.colors.threshold20;
                this.ctx.lineWidth = 3;
            } else if (threshold % 20 === 0) {
                this.ctx.strokeStyle = this.config.colors.gridMajor;
                this.ctx.lineWidth = 1.5;
            } else {
                this.ctx.strokeStyle = this.config.colors.grid;
                this.ctx.lineWidth = 1;
            }
            
            this.ctx.beginPath();
            this.ctx.moveTo(this.config.margin.left, y);
            this.ctx.lineTo(this.config.margin.left + width, y);
            this.ctx.stroke();
        }
    }

    /**
     * Dibujar área de normalidad (0-20 dB HL)
     */
    drawNormalArea(xScale, yScale) {
        this.ctx.fillStyle = this.config.colors.normalArea;
        
        this.ctx.beginPath();
        this.ctx.moveTo(this.config.margin.left, yScale(0));
        this.ctx.lineTo(this.config.margin.left + (this.canvas.width - this.config.margin.left - this.config.margin.right), yScale(0));
        this.ctx.lineTo(this.config.margin.left + (this.canvas.width - this.config.margin.left - this.config.margin.right), yScale(20));
        this.ctx.lineTo(this.config.margin.left, yScale(20));
        this.ctx.closePath();
        this.ctx.fill();
    }

    /**
     * Dibujar ejes y etiquetas
     */
    drawAxes(width, height) {
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'center';

        // Etiquetas eje X (frecuencias) - arriba del gráfico
        this.frequencies.forEach((freq, index) => {
            const x = this.config.margin.left + (index / (this.frequencies.length - 1)) * width;
            const label = freq >= 1000 ? `${freq/1000}k` : freq.toString();
            
            // Destacar frecuencias importantes
            if ([500, 1000, 2000, 4000].includes(freq)) {
                this.ctx.font = 'bold 12px Arial';
                this.ctx.fillStyle = '#333';
            } else {
                this.ctx.font = '11px Arial';
                this.ctx.fillStyle = '#666';
            }
            
            this.ctx.fillText(label, x, this.config.margin.top - 10);
        });

        // Etiquetas eje Y (umbrales)
        this.ctx.textAlign = 'right';
        this.ctx.font = '11px Arial';
        this.ctx.fillStyle = this.config.colors.text;
        
        for (let threshold = 0; threshold <= 120; threshold += 10) {
            const y = this.config.margin.top + (threshold / 120) * height;
            
            // Destacar línea de 20 dB
            if (threshold === 20) {
                this.ctx.font = 'bold 11px Arial';
                this.ctx.fillStyle = this.config.colors.threshold20;
            } else {
                this.ctx.font = '11px Arial';
                this.ctx.fillStyle = this.config.colors.text;
            }
            
            this.ctx.fillText(threshold.toString(), this.config.margin.left - 10, y + 4);
        }

        // Títulos de ejes
        this.ctx.textAlign = 'center';
        this.ctx.font = 'bold 13px Arial';
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.fillText('Frecuencia (Hz)', this.config.margin.left + width/2, this.config.margin.top + height + 45);

        this.ctx.save();
        this.ctx.translate(25, this.config.margin.top + height/2);
        this.ctx.rotate(-Math.PI/2);
        this.ctx.fillText('Umbral (dB HL)', 0, 0);
        this.ctx.restore();

        // Título del gráfico
        this.ctx.font = 'bold 14px Arial';
        this.ctx.fillText('Audiometría de Campo Libre', this.config.margin.left + width/2, 25);
    }

    /**
     * Dibujar datos del audiograma
     */
    drawAudiogramData(data, xScale, yScale) {
        // Dibujar umbrales sin audífonos
        this.drawThresholds(data.sin_audifonos, 'sin_audifonos', xScale, yScale);
        
        // Dibujar umbrales con audífonos (si están disponibles)
        if (data.tiene_audifonos_actuales && data.con_audifonos) {
            this.drawThresholds(data.con_audifonos, 'con_audifonos', xScale, yScale);
        }
    }

    /**
     * Dibujar umbrales de una condición específica
     */
    drawThresholds(thresholdData, condition, xScale, yScale) {
        const ears = [
            { 
                key: 'oido_derecho', 
                color: condition === 'sin_audifonos' ? this.config.colors.od_sin : this.config.colors.od_con,
                symbol: condition === 'sin_audifonos' ? this.symbols.sin_od : this.symbols.con_od
            },
            { 
                key: 'oido_izquierdo', 
                color: condition === 'sin_audifonos' ? this.config.colors.oi_sin : this.config.colors.oi_con,
                symbol: condition === 'sin_audifonos' ? this.symbols.sin_oi : this.symbols.con_oi
            }
        ];

        ears.forEach(ear => {
            const earData = thresholdData?.[ear.key];
            if (!earData) return;

            const points = [];

            // Recopilar puntos válidos
            this.frequencies.forEach((freq, index) => {
                const threshold = earData[freq.toString()];
                if (typeof threshold === 'number' && threshold >= 0 && threshold <= 120) {
                    const x = xScale(index);
                    const y = yScale(threshold);
                    points.push({ x, y, freq, threshold });
                }
            });

            if (points.length === 0) return;

            // Dibujar línea conectora
            if (points.length > 1) {
                this.ctx.strokeStyle = ear.color;
                this.ctx.lineWidth = this.lineStyles[condition].width;
                this.ctx.setLineDash(this.lineStyles[condition].dash);
                
                this.ctx.beginPath();
                points.forEach((point, index) => {
                    if (index === 0) {
                        this.ctx.moveTo(point.x, point.y);
                    } else {
                        this.ctx.lineTo(point.x, point.y);
                    }
                });
                this.ctx.stroke();
                this.ctx.setLineDash([]);
            }

            // Dibujar símbolos de umbrales
            points.forEach(point => {
                this.drawSymbol(point.x, point.y, ear.symbol, ear.color);
            });
        });
    }

    /**
     * Dibujar símbolos audiométricos
     */
    drawSymbol(x, y, symbol, color) {
        this.ctx.fillStyle = color;
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2;

        switch (symbol) {
            case 'circle_open':
                this.ctx.beginPath();
                this.ctx.arc(x, y, 5, 0, 2 * Math.PI);
                this.ctx.stroke();
                break;
            case 'circle_filled':
                this.ctx.beginPath();
                this.ctx.arc(x, y, 5, 0, 2 * Math.PI);
                this.ctx.fill();
                break;
            case 'x':
                this.ctx.beginPath();
                this.ctx.moveTo(x - 5, y - 5);
                this.ctx.lineTo(x + 5, y + 5);
                this.ctx.moveTo(x + 5, y - 5);
                this.ctx.lineTo(x - 5, y + 5);
                this.ctx.stroke();
                break;
            case 'triangle':
                this.ctx.beginPath();
                this.ctx.moveTo(x, y - 5);
                this.ctx.lineTo(x - 4, y + 4);
                this.ctx.lineTo(x + 4, y + 4);
                this.ctx.closePath();
                this.ctx.fill();
                break;
        }
    }

    /**
     * Dibujar ganancia funcional
     */
    drawGananciaFuncional(data, xScale, yScale) {
        if (!data.tiene_audifonos_actuales || !data.sin_audifonos || !data.con_audifonos) return;

        const ears = ['oido_derecho', 'oido_izquierdo'];
        
        ears.forEach((ear, earIndex) => {
            const sinData = data.sin_audifonos[ear];
            const conData = data.con_audifonos[ear];
            
            if (!sinData || !conData) return;

            this.frequencies.forEach((freq, freqIndex) => {
                const sinThreshold = sinData[freq.toString()];
                const conThreshold = conData[freq.toString()];
                
                if (typeof sinThreshold === 'number' && typeof conThreshold === 'number') {
                    const ganancia = sinThreshold - conThreshold;
                    
                    if (ganancia > 0) { // Solo mostrar ganancia positiva
                        const x = xScale(freqIndex);
                        const ySin = yScale(sinThreshold);
                        const yCon = yScale(conThreshold);
                        
                        // Línea de ganancia
                        this.ctx.strokeStyle = this.config.colors.ganancia;
                        this.ctx.lineWidth = 1.5;
                        this.ctx.setLineDash([3, 3]);
                        this.ctx.beginPath();
                        this.ctx.moveTo(x, ySin);
                        this.ctx.lineTo(x, yCon);
                        this.ctx.stroke();
                        this.ctx.setLineDash([]);
                        
                        // Etiqueta de ganancia
                        this.ctx.fillStyle = this.config.colors.ganancia;
                        this.ctx.font = '9px Arial';
                        this.ctx.textAlign = 'center';
                        this.ctx.fillText(`+${ganancia.toFixed(0)}`, x + (earIndex === 0 ? -15 : 15), (ySin + yCon) / 2);
                    }
                }
            });
        });
    }

    /**
     * Dibujar leyenda
     */
    drawLegend(data) {
        const legendY = this.config.margin.top + 10;
        this.ctx.font = '11px Arial';
        this.ctx.textAlign = 'left';

        // Área de normalidad
        this.ctx.fillStyle = this.config.colors.normalArea;
        this.ctx.fillRect(this.config.margin.left, legendY, 15, 8);
        this.ctx.strokeStyle = this.config.colors.threshold20;
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(this.config.margin.left, legendY, 15, 8);
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.fillText('Área normal (0-20 dB HL)', this.config.margin.left + 20, legendY + 6);

        // Símbolos de umbrales
        const symbolY = legendY + 20;
        let xOffset = this.config.margin.left;

        // Sin audífonos
        this.drawSymbol(xOffset + 7, symbolY, 'circle_open', this.config.colors.od_sin);
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.fillText('OD sin', xOffset + 20, symbolY + 3);
        xOffset += 70;

        this.drawSymbol(xOffset + 7, symbolY, 'x', this.config.colors.oi_sin);
        this.ctx.fillText('OI sin', xOffset + 20, symbolY + 3);
        xOffset += 70;

        // Con audífonos (si aplica)
        if (data.tiene_audifonos_actuales) {
            this.drawSymbol(xOffset + 7, symbolY, 'circle_filled', this.config.colors.od_con);
            this.ctx.fillText('OD con', xOffset + 20, symbolY + 3);
            xOffset += 70;

            this.drawSymbol(xOffset + 7, symbolY, 'triangle', this.config.colors.oi_con);
            this.ctx.fillText('OI con', xOffset + 20, symbolY + 3);
            xOffset += 70;

            // Ganancia funcional
            this.ctx.strokeStyle = this.config.colors.ganancia;
            this.ctx.lineWidth = 1.5;
            this.ctx.setLineDash([3, 3]);
            this.ctx.beginPath();
            this.ctx.moveTo(xOffset, symbolY - 3);
            this.ctx.lineTo(xOffset, symbolY + 3);
            this.ctx.stroke();
            this.ctx.setLineDash([]);
            this.ctx.fillText('Ganancia', xOffset + 10, symbolY + 3);
        }
    }

    /**
     * Dibujar información de campo libre
     */
    drawFieldAudioInfo(data) {
        const infoY = this.canvas.height - 50;
        this.ctx.font = '11px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillStyle = this.config.colors.text;

        let infoLines = [];

        // SRT información
        if (data.srt_discriminacion?.sin_audifonos) {
            const srtSin = data.srt_discriminacion.sin_audifonos;
            if (srtSin.srt_od || srtSin.srt_oi) {
                let srtText = 'SRT sin audífonos:';
                if (srtSin.srt_od) srtText += ` OD=${srtSin.srt_od}dB`;
                if (srtSin.srt_oi) srtText += ` OI=${srtSin.srt_oi}dB`;
                infoLines.push(srtText);
            }
        }

        if (data.srt_discriminacion?.con_audifonos && data.tiene_audifonos_actuales) {
            const srtCon = data.srt_discriminacion.con_audifonos;
            if (srtCon.srt_od || srtCon.srt_oi) {
                let srtText = 'SRT con audífonos:';
                if (srtCon.srt_od) srtText += ` OD=${srtCon.srt_od}dB`;
                if (srtCon.srt_oi) srtText += ` OI=${srtCon.srt_oi}dB`;
                infoLines.push(srtText);
            }
        }

        // Discriminación
        if (data.srt_discriminacion?.sin_audifonos) {
            const discSin = data.srt_discriminacion.sin_audifonos;
            if (discSin.disc_od || discSin.disc_oi) {
                let discText = 'Discriminación sin:';
                if (discSin.disc_od) discText += ` OD=${discSin.disc_od}%`;
                if (discSin.disc_oi) discText += ` OI=${discSin.disc_oi}%`;
                infoLines.push(discText);
            }
        }

        // Mostrar información
        infoLines.forEach((line, index) => {
            this.ctx.fillText(line, this.config.margin.left, infoY + (index * 15));
        });

        // Ganancia funcional promedio
        if (data.tiene_audifonos_actuales) {
            this.drawGananciaPromedio(data, infoY);
        }
    }

    /**
     * Calcular y mostrar ganancia funcional promedio
     */
    drawGananciaPromedio(data, startY) {
        const promedios = this.calculateGananciaPromedio(data);
        
        if (promedios.od !== null || promedios.oi !== null) {
            const promedioX = this.canvas.width - 200;
            this.ctx.font = 'bold 11px Arial';
            this.ctx.textAlign = 'left';
            this.ctx.fillStyle = this.config.colors.ganancia;
            
            let promedioText = 'Ganancia funcional promedio: ';
            if (promedios.od !== null) promedioText += `OD=${promedios.od.toFixed(1)}dB `;
            if (promedios.oi !== null) promedioText += `OI=${promedios.oi.toFixed(1)}dB`;
            
            this.ctx.fillText(promedioText, promedioX, startY);
        }
    }

    /**
     * Calcular ganancia funcional promedio
     */
    calculateGananciaPromedio(data) {
        const ears = ['oido_derecho', 'oido_izquierdo'];
        const promedios = { od: null, oi: null };
        
        ears.forEach((ear, index) => {
            const sinData = data.sin_audifonos?.[ear];
            const conData = data.con_audifonos?.[ear];
            
            if (!sinData || !conData) return;
            
            const ganancias = [];
            this.frequencies.forEach(freq => {
                const sinThreshold = sinData[freq.toString()];
                const conThreshold = conData[freq.toString()];
                
                if (typeof sinThreshold === 'number' && typeof conThreshold === 'number') {
                    const ganancia = sinThreshold - conThreshold;
                    if (ganancia > 0) {
                        ganancias.push(ganancia);
                    }
                }
            });
            
            if (ganancias.length > 0) {
                const promedio = ganancias.reduce((sum, g) => sum + g, 0) / ganancias.length;
                promedios[index === 0 ? 'od' : 'oi'] = promedio;
            }
        });
        
        return promedios;
    }

    /**
     * Actualizar datos sin recrear el canvas
     */
    update(data) {
        this.render(data);
    }

    /**
     * Redimensionar canvas
     */
    resize(width, height) {
        if (this.canvas) {
            this.canvas.width = width;
            this.canvas.height = height;
        }
    }

    /**
     * Limpiar canvas
     */
    clear() {
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }

    /**
     * Exportar datos del audiograma
     */
    exportAudiogramData(data) {
        return {
            frequencies: this.frequencies,
            gananciaPrmoedio: this.calculateGananciaPromedio(data),
            symbols: this.symbols,
            hasHearingAids: data.tiene_audifonos_actuales
        };
    }
}

// Exponer globalmente
window.FieldAudiometryChartView = FieldAudiometryChartView;