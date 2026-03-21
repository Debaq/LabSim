/**
 * REMChartView - Vista de Mediciones en Oído Real
 * Gráfico de REIG y REAR vs targets prescriptivos
 */

class REMChartView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.canvas = null;
        this.ctx = null;
        this.config = {
            margin: { top: 40, right: 50, bottom: 60, left: 70 },
            colors: {
                od: '#dc3545',
                oi: '#007bff',
                target: '#28a745',
                targetArea: 'rgba(40, 167, 69, 0.1)',
                grid: '#e0e0e0',
                gridMajor: '#ccc',
                text: '#333',
                tolerance: 'rgba(40, 167, 69, 0.2)'
            }
        };

        // Frecuencias para REM (logarítmicas)
        this.frequencies = [250, 500, 1000, 2000, 4000, 8000];
        
        // Datos normativos de targets por fórmula
        this.targetData = {
            nal_nl2: {
                250: { mild: 15, moderate: 25, severe: 40 },
                500: { mild: 18, moderate: 30, severe: 45 },
                1000: { mild: 20, moderate: 35, severe: 50 },
                2000: { mild: 22, moderate: 40, severe: 55 },
                4000: { mild: 25, moderate: 45, severe: 60 },
                8000: { mild: 20, moderate: 35, severe: 50 }
            },
            dsl_v5: {
                250: { mild: 12, moderate: 22, severe: 37 },
                500: { mild: 15, moderate: 27, severe: 42 },
                1000: { mild: 17, moderate: 32, severe: 47 },
                2000: { mild: 20, moderate: 37, severe: 52 },
                4000: { mild: 23, moderate: 42, severe: 57 },
                8000: { mild: 18, moderate: 32, severe: 47 }
            }
        };

        // Tolerancia para targets (±5 dB)
        this.tolerance = 5;
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
     * Renderizar gráfico con datos REM
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
        const yScale = (gain) => this.config.margin.top + plotHeight - ((gain + 10) / 80) * plotHeight; // -10 a 70 dB

        // Dibujar componentes
        this.drawGrid(plotWidth, plotHeight, xScale, yScale);
        this.drawTargetArea(data, xScale, yScale);
        this.drawAxes(plotWidth, plotHeight);
        this.drawREIGData(data, xScale, yScale);
        this.drawLegend(data);
        this.drawMatchInfo(data);
    }

    /**
     * Dibujar grilla del gráfico
     */
    drawGrid(width, height, xScale, yScale) {
        this.ctx.strokeStyle = this.config.colors.grid;
        this.ctx.lineWidth = 1;

        // Líneas verticales (frecuencias)
        this.frequencies.forEach((freq, index) => {
            const x = xScale(index);
            
            // Líneas más gruesas para frecuencias clave (1k, 2k, 4k)
            if ([1000, 2000, 4000].includes(freq)) {
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

        // Líneas horizontales (ganancia - cada 10 dB)
        for (let gain = -10; gain <= 70; gain += 10) {
            const y = yScale(gain);
            
            // Línea más gruesa en 0 dB
            if (gain === 0) {
                this.ctx.strokeStyle = this.config.colors.gridMajor;
                this.ctx.lineWidth = 2;
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
     * Dibujar área de target con tolerancia
     */
    drawTargetArea(data, xScale, yScale) {
        const formula = data.formula_prescriptiva;
        if (!formula || !this.targetData[formula]) return;

        const targets = this.targetData[formula];
        
        // Determinar nivel de pérdida basado en datos (simplificado)
        const lossLevel = this.estimateLossLevel(data);
        
        this.ctx.fillStyle = this.config.colors.tolerance;
        this.ctx.strokeStyle = this.config.colors.target;
        this.ctx.lineWidth = 2;

        // Crear path para área de tolerancia
        this.ctx.beginPath();
        
        // Línea superior (target + tolerancia)
        this.frequencies.forEach((freq, index) => {
            const targetValue = targets[freq] ? targets[freq][lossLevel] : 0;
            const x = xScale(index);
            const y = yScale(targetValue + this.tolerance);
            
            if (index === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        });
        
        // Línea inferior (target - tolerancia) - en reversa
        for (let i = this.frequencies.length - 1; i >= 0; i--) {
            const freq = this.frequencies[i];
            const targetValue = targets[freq] ? targets[freq][lossLevel] : 0;
            const x = xScale(i);
            const y = yScale(targetValue - this.tolerance);
            this.ctx.lineTo(x, y);
        }
        
        this.ctx.closePath();
        this.ctx.fill();

        // Dibujar línea de target
        this.ctx.beginPath();
        this.frequencies.forEach((freq, index) => {
            const targetValue = targets[freq] ? targets[freq][lossLevel] : 0;
            const x = xScale(index);
            const y = yScale(targetValue);
            
            if (index === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        });
        this.ctx.stroke();
    }

    /**
     * Estimar nivel de pérdida auditiva basado en datos REIG
     */
    estimateLossLevel(data) {
        // Calcular promedio de ganancia REIG para estimar severidad
        let totalGain = 0;
        let count = 0;

        ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
            const earData = data.reig?.[ear];
            if (earData) {
                Object.values(earData).forEach(gain => {
                    if (typeof gain === 'number') {
                        totalGain += gain;
                        count++;
                    }
                });
            }
        });

        if (count === 0) return 'mild';

        const avgGain = totalGain / count;
        
        // Clasificar según ganancia promedio
        if (avgGain < 20) return 'mild';
        if (avgGain < 35) return 'moderate';
        return 'severe';
    }

    /**
     * Dibujar ejes y etiquetas
     */
    drawAxes(width, height) {
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'center';

        // Etiquetas eje X (frecuencias)
        this.frequencies.forEach((freq, index) => {
            const x = this.config.margin.left + (index / (this.frequencies.length - 1)) * width;
            const label = freq >= 1000 ? `${freq/1000}k` : freq.toString();
            
            // Destacar frecuencias clave
            if ([1000, 2000, 4000].includes(freq)) {
                this.ctx.font = 'bold 12px Arial';
                this.ctx.fillStyle = '#333';
            } else {
                this.ctx.font = '11px Arial';
                this.ctx.fillStyle = '#666';
            }
            
            this.ctx.fillText(label, x, this.config.margin.top + height + 20);
        });

        // Etiquetas eje Y (ganancia)
        this.ctx.textAlign = 'right';
        this.ctx.font = '11px Arial';
        this.ctx.fillStyle = this.config.colors.text;
        
        for (let gain = -10; gain <= 70; gain += 10) {
            const y = this.config.margin.top + height - ((gain + 10) / 80) * height;
            this.ctx.fillText(`${gain}`, this.config.margin.left - 10, y + 4);
        }

        // Títulos de ejes
        this.ctx.textAlign = 'center';
        this.ctx.font = 'bold 13px Arial';
        this.ctx.fillText('Frecuencia (Hz)', this.config.margin.left + width/2, this.config.margin.top + height + 45);

        this.ctx.save();
        this.ctx.translate(25, this.config.margin.top + height/2);
        this.ctx.rotate(-Math.PI/2);
        this.ctx.fillText('Ganancia REIG (dB)', 0, 0);
        this.ctx.restore();

        // Título del gráfico
        this.ctx.font = 'bold 14px Arial';
        this.ctx.fillText('REIG vs Target Prescriptivo', this.config.margin.left + width/2, 25);
    }

    /**
     * Dibujar datos REIG
     */
    drawREIGData(data, xScale, yScale) {
        const ears = [
            { key: 'oido_derecho', color: this.config.colors.od, label: 'OD', symbol: 'circle' },
            { key: 'oido_izquierdo', color: this.config.colors.oi, label: 'OI', symbol: 'square' }
        ];

        ears.forEach(ear => {
            const earData = data.reig?.[ear];
            if (!earData) return;

            const points = [];

            // Recopilar puntos de datos
            this.frequencies.forEach((freq, index) => {
                const gain = earData[freq.toString()];
                if (typeof gain === 'number') {
                    const x = xScale(index);
                    const y = yScale(gain);
                    points.push({ x, y, freq, gain });
                }
            });

            if (points.length === 0) return;

            // Dibujar línea conectora
            if (points.length > 1) {
                this.ctx.strokeStyle = ear.color;
                this.ctx.lineWidth = 2.5;
                this.ctx.setLineDash([]);
                
                this.ctx.beginPath();
                points.forEach((point, index) => {
                    if (index === 0) {
                        this.ctx.moveTo(point.x, point.y);
                    } else {
                        this.ctx.lineTo(point.x, point.y);
                    }
                });
                this.ctx.stroke();
            }

            // Dibujar símbolos de datos
            points.forEach(point => {
                this.drawSymbol(point.x, point.y, ear.symbol, ear.color);
            });
        });
    }

    /**
     * Dibujar símbolos de datos
     */
    drawSymbol(x, y, symbol, color) {
        this.ctx.fillStyle = color;
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2;

        switch (symbol) {
            case 'circle':
                this.ctx.beginPath();
                this.ctx.arc(x, y, 5, 0, 2 * Math.PI);
                this.ctx.fill();
                break;
            case 'square':
                this.ctx.fillRect(x - 4, y - 4, 8, 8);
                break;
        }
    }

    /**
     * Dibujar leyenda
     */
    drawLegend(data) {
        const legendY = this.config.margin.top + 10;
        this.ctx.font = '11px Arial';
        this.ctx.textAlign = 'left';

        // Área de target
        this.ctx.fillStyle = this.config.colors.tolerance;
        this.ctx.fillRect(this.config.margin.left, legendY, 15, 8);
        this.ctx.strokeStyle = this.config.colors.target;
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(this.config.margin.left, legendY, 15, 8);
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.fillText(`Target ±${this.tolerance}dB`, this.config.margin.left + 20, legendY + 6);

        // Fórmula prescriptiva
        if (data.formula_prescriptiva) {
            const formulaName = data.formula_prescriptiva.toUpperCase().replace('_', '-');
            this.ctx.fillText(`(${formulaName})`, this.config.margin.left + 120, legendY + 6);
        }

        // Símbolos de oídos
        const symbolY = legendY + 20;
        
        // OD
        this.drawSymbol(this.config.margin.left + 7, symbolY, 'circle', this.config.colors.od);
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.fillText('OD', this.config.margin.left + 20, symbolY + 3);

        // OI
        this.drawSymbol(this.config.margin.left + 60, symbolY, 'square', this.config.colors.oi);
        this.ctx.fillText('OI', this.config.margin.left + 73, symbolY + 3);
    }

    /**
     * Dibujar información de match
     */
    drawMatchInfo(data) {
        if (!data.match_target && !data.desviacion_rms) return;

        const infoY = this.canvas.height - 30;
        this.ctx.font = '11px Arial';
        this.ctx.textAlign = 'right';
        this.ctx.fillStyle = this.config.colors.text;

        let infoText = '';
        if (data.match_target) {
            infoText += `Match: ${data.match_target}%`;
        }
        if (data.desviacion_rms) {
            if (infoText) infoText += ' | ';
            infoText += `RMS: ${data.desviacion_rms}dB`;
        }

        this.ctx.fillText(infoText, this.canvas.width - 20, infoY);
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
     * Configurar canvas para múltiples gráficos
     */
    setMode(mode) {
        // Permitir alternar entre REIG y REAR
        this.mode = mode || 'reig';
        
        if (this.mode === 'rear') {
            // Ajustar escala Y para REAR (50-130 dB SPL)
            this.yRange = { min: 50, max: 130 };
        } else {
            // REIG (ganancia -10 a 70 dB)
            this.yRange = { min: -10, max: 70 };
        }
    }

    /**
     * Exportar datos del gráfico
     */
    exportData() {
        // Retornar datos para análisis posterior
        return {
            frequencies: this.frequencies,
            targets: this.targetData,
            tolerance: this.tolerance,
            mode: this.mode || 'reig'
        };
    }
}

// Exponer globalmente
window.REMChartView = REMChartView;