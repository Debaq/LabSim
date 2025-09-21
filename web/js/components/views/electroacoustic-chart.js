/**
 * ElectroacousticChartView - Vista de Curvas Electroacústicas
 * Respuesta en frecuencia, curvas de saturación y características técnicas
 */

class ElectroacousticChartView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.canvas = null;
        this.ctx = null;
        this.config = {
            margin: { top: 40, right: 50, bottom: 60, left: 70 },
            colors: {
                od: '#dc3545',
                oi: '#007bff',
                reference: '#28a745',
                saturation: '#ff6b35',
                grid: '#e0e0e0',
                gridMajor: '#ccc',
                text: '#333',
                normalArea: 'rgba(40, 167, 69, 0.1)',
                limitLine: '#ffc107'
            }
        };

        // Frecuencias para electroacústica (más detalladas)
        this.frequencies = [250, 500, 1000, 2000, 4000, 8000];
        
        // Datos normativos para audífonos (basados en estándares IEC)
        this.normativeData = {
            // Ganancia de referencia típica por gama
            referenceGain: {
                basico: { 250: 15, 500: 20, 1000: 25, 2000: 30, 4000: 25, 8000: 15 },
                intermedio: { 250: 18, 500: 25, 1000: 30, 2000: 35, 4000: 30, 8000: 20 },
                avanzado: { 250: 20, 500: 28, 1000: 35, 2000: 40, 8000: 25 },
                premium: { 250: 22, 500: 30, 1000: 38, 2000: 42, 4000: 35, 8000: 28 }
            },
            // Límites de distorsión aceptables
            thdLimits: {
                500: 3.0,  // % THD máximo a 500 Hz
                800: 3.5,  // % THD máximo a 800 Hz
                1600: 5.0  // % THD máximo a 1600 Hz
            },
            // Rangos típicos por tipo de audífono
            ranges: {
                bte: { gainMin: 10, gainMax: 80, osplMax: 135 },
                ric_rite: { gainMin: 8, gainMax: 65, osplMax: 125 },
                ite: { gainMin: 5, gainMax: 55, osplMax: 120 },
                itc: { gainMin: 5, gainMax: 45, osplMax: 115 },
                cic: { gainMin: 3, gainMax: 35, osplMax: 110 }
            }
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
     * Renderizar gráfico con datos electroacústicos
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
        const yScale = (gain) => this.config.margin.top + plotHeight - ((gain + 10) / 90) * plotHeight; // -10 a 80 dB

        // Dibujar componentes
        this.drawGrid(plotWidth, plotHeight, xScale, yScale);
        this.drawReferenceArea(data, xScale, yScale);
        this.drawSaturationLine(data, xScale, yScale);
        this.drawAxes(plotWidth, plotHeight);
        this.drawFrequencyResponse(data, xScale, yScale);
        this.drawLegend(data);
        this.drawTechnicalInfo(data);
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
            
            // Líneas más gruesas para frecuencias estándar (500, 1k, 2k, 4k)
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

        // Líneas horizontales (ganancia - cada 10 dB)
        for (let gain = -10; gain <= 80; gain += 10) {
            const y = yScale(gain);
            
            // Líneas más gruesas en 0 y 40 dB (referencias importantes)
            if (gain === 0 || gain === 40) {
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
     * Dibujar área de ganancia de referencia
     */
    drawReferenceArea(data, xScale, yScale) {
        // Usar ganancia HFA como referencia si está disponible
        const hfaGain = data.ganancia_hfa;
        if (!hfaGain) return;

        // Estimar gama basada en ganancia HFA
        const estimatedRange = this.estimateHearingAidRange(hfaGain);
        const referenceGains = this.normativeData.referenceGain[estimatedRange];

        this.ctx.fillStyle = this.config.colors.normalArea;
        this.ctx.strokeStyle = this.config.colors.reference;
        this.ctx.lineWidth = 1.5;
        this.ctx.setLineDash([5, 5]);

        // Dibujar área de referencia (±10 dB)
        this.ctx.beginPath();
        
        // Línea superior
        this.frequencies.forEach((freq, index) => {
            const refGain = referenceGains[freq] || hfaGain;
            const x = xScale(index);
            const y = yScale(refGain + 10);
            
            if (index === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        });
        
        // Línea inferior (reversa)
        for (let i = this.frequencies.length - 1; i >= 0; i--) {
            const freq = this.frequencies[i];
            const refGain = referenceGains[freq] || hfaGain;
            const x = xScale(i);
            const y = yScale(refGain - 10);
            this.ctx.lineTo(x, y);
        }
        
        this.ctx.closePath();
        this.ctx.fill();

        // Línea de referencia central
        this.ctx.beginPath();
        this.frequencies.forEach((freq, index) => {
            const refGain = referenceGains[freq] || hfaGain;
            const x = xScale(index);
            const y = yScale(refGain);
            
            if (index === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        });
        this.ctx.stroke();
        this.ctx.setLineDash([]);
    }

    /**
     * Estimar gama del audífono basado en ganancia HFA
     */
    estimateHearingAidRange(hfaGain) {
        if (hfaGain < 20) return 'basico';
        if (hfaGain < 30) return 'intermedio';
        if (hfaGain < 40) return 'avanzado';
        return 'premium';
    }

    /**
     * Dibujar línea de saturación (OSPL90)
     */
    drawSaturationLine(data, xScale, yScale) {
        const ospl90 = data.ospl90;
        if (!ospl90) return;

        // Convertir OSPL90 a ganancia equivalente (estimación)
        const estimatedSatGain = Math.max(0, ospl90 - 90); // Simplificado

        this.ctx.strokeStyle = this.config.colors.saturation;
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([10, 5]);

        const y = yScale(estimatedSatGain);
        this.ctx.beginPath();
        this.ctx.moveTo(this.config.margin.left, y);
        this.ctx.lineTo(this.config.margin.left + (this.canvas.width - this.config.margin.left - this.config.margin.right), y);
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        // Etiqueta OSPL90
        this.ctx.fillStyle = this.config.colors.saturation;
        this.ctx.font = '11px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`OSPL90: ${ospl90} dB SPL`, this.config.margin.left + 10, y - 5);
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
            
            // Destacar frecuencias importantes para audífonos
            if ([500, 1000, 2000, 4000].includes(freq)) {
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
        
        for (let gain = -10; gain <= 80; gain += 10) {
            const y = this.config.margin.top + height - ((gain + 10) / 90) * height;
            this.ctx.fillText(`${gain}`, this.config.margin.left - 10, y + 4);
        }

        // Títulos de ejes
        this.ctx.textAlign = 'center';
        this.ctx.font = 'bold 13px Arial';
        this.ctx.fillText('Frecuencia (Hz)', this.config.margin.left + width/2, this.config.margin.top + height + 45);

        this.ctx.save();
        this.ctx.translate(25, this.config.margin.top + height/2);
        this.ctx.rotate(-Math.PI/2);
        this.ctx.fillText('Ganancia (dB)', 0, 0);
        this.ctx.restore();

        // Título del gráfico
        this.ctx.font = 'bold 14px Arial';
        this.ctx.fillText('Respuesta en Frecuencia - Mediciones Electroacústicas', this.config.margin.left + width/2, 25);
    }

    /**
     * Dibujar respuesta en frecuencia medida
     */
    drawFrequencyResponse(data, xScale, yScale) {
        const ears = [
            { key: 'oido_derecho', color: this.config.colors.od, label: 'OD', symbol: 'circle' },
            { key: 'oido_izquierdo', color: this.config.colors.oi, label: 'OI', symbol: 'triangle' }
        ];

        ears.forEach(ear => {
            const earData = data.respuesta_frecuencia?.[ear.key];
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

            // Dibujar línea conectora con curva suave
            if (points.length > 1) {
                this.ctx.strokeStyle = ear.color;
                this.ctx.lineWidth = 3;
                this.ctx.setLineDash([]);
                
                this.drawSmoothCurve(points);
            }

            // Dibujar símbolos de datos
            points.forEach(point => {
                this.drawSymbol(point.x, point.y, ear.symbol, ear.color);
                
                // Mostrar valor en el punto
                this.ctx.fillStyle = ear.color;
                this.ctx.font = '9px Arial';
                this.ctx.textAlign = 'center';
                this.ctx.fillText(point.gain.toString(), point.x, point.y - 12);
            });
        });
    }

    /**
     * Dibujar curva suave entre puntos
     */
    drawSmoothCurve(points) {
        this.ctx.beginPath();
        this.ctx.moveTo(points[0].x, points[0].y);

        for (let i = 0; i < points.length - 1; i++) {
            const current = points[i];
            const next = points[i + 1];
            
            // Puntos de control para curva Bézier
            const cp1x = current.x + (next.x - current.x) * 0.4;
            const cp1y = current.y;
            const cp2x = next.x - (next.x - current.x) * 0.4;
            const cp2y = next.y;
            
            this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, next.x, next.y);
        }

        this.ctx.stroke();
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
                this.ctx.arc(x, y, 6, 0, 2 * Math.PI);
                this.ctx.fill();
                this.ctx.stroke();
                break;
            case 'triangle':
                this.ctx.beginPath();
                this.ctx.moveTo(x, y - 6);
                this.ctx.lineTo(x - 5, y + 4);
                this.ctx.lineTo(x + 5, y + 4);
                this.ctx.closePath();
                this.ctx.fill();
                this.ctx.stroke();
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

        // Área de referencia
        if (data.ganancia_hfa) {
            this.ctx.fillStyle = this.config.colors.normalArea;
            this.ctx.fillRect(this.config.margin.left, legendY, 15, 8);
            this.ctx.strokeStyle = this.config.colors.reference;
            this.ctx.lineWidth = 1;
            this.ctx.setLineDash([3, 3]);
            this.ctx.strokeRect(this.config.margin.left, legendY, 15, 8);
            this.ctx.setLineDash([]);
            this.ctx.fillStyle = this.config.colors.text;
            this.ctx.fillText('Rango de referencia ±10dB', this.config.margin.left + 20, legendY + 6);
        }

        // Símbolos de oídos
        const symbolY = legendY + 20;
        
        // OD
        this.drawSymbol(this.config.margin.left + 7, symbolY, 'circle', this.config.colors.od);
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.fillText('OD', this.config.margin.left + 20, symbolY + 3);

        // OI
        this.drawSymbol(this.config.margin.left + 60, symbolY, 'triangle', this.config.colors.oi);
        this.ctx.fillText('OI', this.config.margin.left + 73, symbolY + 3);

        // Línea de saturación
        if (data.ospl90) {
            this.ctx.strokeStyle = this.config.colors.saturation;
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([5, 3]);
            this.ctx.beginPath();
            this.ctx.moveTo(this.config.margin.left + 120, symbolY);
            this.ctx.lineTo(this.config.margin.left + 135, symbolY);
            this.ctx.stroke();
            this.ctx.setLineDash([]);
            this.ctx.fillText('Saturación', this.config.margin.left + 140, symbolY + 3);
        }
    }

    /**
     * Dibujar información técnica
     */
    drawTechnicalInfo(data) {
        const infoY = this.canvas.height - 40;
        this.ctx.font = '11px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillStyle = this.config.colors.text;

        let infoLines = [];
        
        // HFA y OSPL90
        if (data.ganancia_hfa) {
            infoLines.push(`HFA: ${data.ganancia_hfa} dB`);
        }
        if (data.ospl90) {
            infoLines.push(`OSPL90: ${data.ospl90} dB SPL`);
        }

        // THD
        if (data.thd_500 || data.thd_800) {
            let thdText = 'THD:';
            if (data.thd_500) thdText += ` 500Hz=${data.thd_500}%`;
            if (data.thd_800) thdText += ` 800Hz=${data.thd_800}%`;
            infoLines.push(thdText);
        }

        // EIN y corriente
        if (data.ruido_ein) {
            infoLines.push(`EIN: ${data.ruido_ein} dB SPL`);
        }
        if (data.corriente_bateria) {
            infoLines.push(`Corriente: ${data.corriente_bateria} mA`);
        }

        // Mostrar información en líneas
        infoLines.forEach((line, index) => {
            this.ctx.fillText(line, this.config.margin.left, infoY + (index * 15));
        });

        // Indicadores de calidad (semáforo)
        this.drawQualityIndicators(data, infoY);
    }

    /**
     * Dibujar indicadores de calidad
     */
    drawQualityIndicators(data, startY) {
        const indicatorX = this.canvas.width - 150;
        this.ctx.font = 'bold 10px Arial';
        this.ctx.textAlign = 'left';

        // THD Status
        if (data.thd_500 || data.thd_800) {
            const maxThd = Math.max(data.thd_500 || 0, data.thd_800 || 0);
            const thdColor = maxThd <= 3 ? '#28a745' : maxThd <= 5 ? '#ffc107' : '#dc3545';
            const thdStatus = maxThd <= 3 ? 'BUENO' : maxThd <= 5 ? 'ACEPTABLE' : 'ALTO';
            
            this.ctx.fillStyle = thdColor;
            this.ctx.fillRect(indicatorX, startY, 12, 12);
            this.ctx.fillStyle = this.config.colors.text;
            this.ctx.fillText(`THD: ${thdStatus}`, indicatorX + 18, startY + 9);
        }

        // EIN Status
        if (data.ruido_ein) {
            const einColor = data.ruido_ein <= 25 ? '#28a745' : data.ruido_ein <= 30 ? '#ffc107' : '#dc3545';
            const einStatus = data.ruido_ein <= 25 ? 'BUENO' : data.ruido_ein <= 30 ? 'ACEPTABLE' : 'ALTO';
            
            this.ctx.fillStyle = einColor;
            this.ctx.fillRect(indicatorX, startY + 15, 12, 12);
            this.ctx.fillStyle = this.config.colors.text;
            this.ctx.fillText(`Ruido: ${einStatus}`, indicatorX + 18, startY + 24);
        }
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
     * Exportar configuración del gráfico
     */
    exportConfig() {
        return {
            frequencies: this.frequencies,
            normativeData: this.normativeData,
            mode: 'frequency_response'
        };
    }
}

// Exponer globalmente
window.ElectroacousticChartView = ElectroacousticChartView;