/**
 * CompressionChartView - Vista de Curvas de Compresión
 * Características de entrada/salida, knee points y comportamiento dinámico
 */

class CompressionChartView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.canvas = null;
        this.ctx = null;
        this.config = {
            margin: { top: 40, right: 50, bottom: 60, left: 70 },
            colors: {
                inputOutput: '#2a5298',
                linear: '#28a745',
                kneePoint: '#dc3545',
                compressionZone: 'rgba(42, 82, 152, 0.1)',
                grid: '#e0e0e0',
                gridMajor: '#ccc',
                text: '#333',
                threshold: '#ffc107',
                limitLine: '#ff6b35'
            }
        };

        // Rangos típicos para audífonos
        this.ranges = {
            input: { min: 40, max: 90 },    // dB SPL entrada
            output: { min: 50, max: 120 },  // dB SPL salida
            compression: [1.5, 2, 3, 4, 6, 10] // Ratios típicos
        };

        // Datos normativos de compresión
        this.normativeData = {
            // Puntos típicos de knee por severidad de pérdida
            kneePoints: {
                mild: 55,     // dB SPL
                moderate: 50,
                severe: 45,
                profound: 40
            },
            // Ratios recomendados por severidad
            recommendedRatios: {
                mild: 2,
                moderate: 3,
                severe: 4,
                profound: 6
            },
            // Tiempos típicos
            attackTimes: { fast: 5, medium: 10, slow: 20 }, // ms
            releaseTimes: { fast: 50, medium: 150, slow: 500 } // ms
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
     * Renderizar gráfico con datos de compresión
     */
    render(data) {
        if (!this.init()) return;

        // Limpiar canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Configuración del área de dibujo
        const plotWidth = this.canvas.width - this.config.margin.left - this.config.margin.right;
        const plotHeight = this.canvas.height - this.config.margin.top - this.config.margin.bottom;

        // Funciones de escala
        const xScale = (inputLevel) => this.config.margin.left + ((inputLevel - 40) / 50) * plotWidth; // 40-90 dB input
        const yScale = (outputLevel) => this.config.margin.top + plotHeight - ((outputLevel - 50) / 70) * plotHeight; // 50-120 dB output

        // Dibujar componentes
        this.drawGrid(plotWidth, plotHeight, xScale, yScale);
        this.drawLinearReference(xScale, yScale);
        this.drawCompressionZone(data, xScale, yScale);
        this.drawAxes(plotWidth, plotHeight);
        this.drawCompressionCurve(data, xScale, yScale);
        this.drawKneePoint(data, xScale, yScale);
        this.drawLegend(data);
        this.drawCompressionInfo(data);
    }

    /**
     * Dibujar grilla del gráfico
     */
    drawGrid(width, height, xScale, yScale) {
        this.ctx.strokeStyle = this.config.colors.grid;
        this.ctx.lineWidth = 1;

        // Líneas verticales (entrada - cada 5 dB)
        for (let input = 40; input <= 90; input += 5) {
            const x = xScale(input);
            
            // Líneas más gruesas cada 10 dB
            if (input % 10 === 0) {
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
        }

        // Líneas horizontales (salida - cada 5 dB)
        for (let output = 50; output <= 120; output += 5) {
            const y = yScale(output);
            
            // Líneas más gruesas cada 10 dB
            if (output % 10 === 0) {
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
     * Dibujar línea de referencia lineal (1:1)
     */
    drawLinearReference(xScale, yScale) {
        this.ctx.strokeStyle = this.config.colors.linear;
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([8, 4]);

        this.ctx.beginPath();
        // Línea 1:1 desde (40,90) hasta (90,140) pero limitada al rango visible
        this.ctx.moveTo(xScale(40), yScale(90));   // 40 dB in → 90 dB out (ganancia 50)
        this.ctx.lineTo(xScale(70), yScale(120));  // 70 dB in → 120 dB out (ganancia 50)
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        // Etiqueta
        this.ctx.fillStyle = this.config.colors.linear;
        this.ctx.font = '10px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText('Lineal (1:1)', xScale(42), yScale(95));
    }

    /**
     * Dibujar zona de compresión
     */
    drawCompressionZone(data, xScale, yScale) {
        const kneePoint = data.knee_point || 55;
        const ratio = this.parseCompressionRatio(data.compression_ratio) || 2;

        // Área sombreada para zona de compresión
        this.ctx.fillStyle = this.config.colors.compressionZone;
        this.ctx.strokeStyle = this.config.colors.threshold;
        this.ctx.lineWidth = 1;

        // Calcular puntos de la zona de compresión
        const compressionStart = kneePoint;
        const compressionEnd = 85; // dB SPL

        this.ctx.beginPath();
        this.ctx.moveTo(xScale(compressionStart), yScale(50));
        this.ctx.lineTo(xScale(compressionEnd), yScale(50));
        this.ctx.lineTo(xScale(compressionEnd), yScale(120));
        this.ctx.lineTo(xScale(compressionStart), yScale(120));
        this.ctx.closePath();
        this.ctx.fill();

        // Línea de umbral de compresión
        this.ctx.strokeStyle = this.config.colors.threshold;
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        this.ctx.beginPath();
        this.ctx.moveTo(xScale(kneePoint), this.config.margin.top);
        this.ctx.lineTo(xScale(kneePoint), this.config.margin.top + (this.canvas.height - this.config.margin.top - this.config.margin.bottom));
        this.ctx.stroke();
        this.ctx.setLineDash([]);
    }

    /**
     * Parsear ratio de compresión desde string
     */
    parseCompressionRatio(ratioString) {
        if (!ratioString) return null;
        const match = ratioString.match(/(\d+(?:\.\d+)?)/);
        return match ? parseFloat(match[1]) : null;
    }

    /**
     * Dibujar ejes y etiquetas
     */
    drawAxes(width, height) {
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.font = '11px Arial';
        this.ctx.textAlign = 'center';

        // Etiquetas eje X (entrada)
        for (let input = 40; input <= 90; input += 10) {
            const x = this.config.margin.left + ((input - 40) / 50) * width;
            this.ctx.fillText(input.toString(), x, this.config.margin.top + height + 20);
        }

        // Etiquetas eje Y (salida)
        this.ctx.textAlign = 'right';
        for (let output = 60; output <= 120; output += 10) {
            const y = this.config.margin.top + height - ((output - 50) / 70) * height;
            this.ctx.fillText(output.toString(), this.config.margin.left - 10, y + 4);
        }

        // Títulos de ejes
        this.ctx.textAlign = 'center';
        this.ctx.font = 'bold 12px Arial';
        this.ctx.fillText('Nivel de Entrada (dB SPL)', this.config.margin.left + width/2, this.config.margin.top + height + 45);

        this.ctx.save();
        this.ctx.translate(25, this.config.margin.top + height/2);
        this.ctx.rotate(-Math.PI/2);
        this.ctx.fillText('Nivel de Salida (dB SPL)', 0, 0);
        this.ctx.restore();

        // Título del gráfico
        this.ctx.font = 'bold 14px Arial';
        this.ctx.fillText('Características de Compresión (I/O)', this.config.margin.left + width/2, 25);
    }

    /**
     * Dibujar curva de compresión
     */
    drawCompressionCurve(data, xScale, yScale) {
        const kneePoint = data.knee_point || 55;
        const ratio = this.parseCompressionRatio(data.compression_ratio) || 2;
        const gainHFA = data.ganancia_hfa || 30; // Ganancia de referencia

        this.ctx.strokeStyle = this.config.colors.inputOutput;
        this.ctx.lineWidth = 3;
        this.ctx.setLineDash([]);

        this.ctx.beginPath();

        // Generar puntos de la curva
        const points = [];
        for (let input = 40; input <= 90; input += 2) {
            let output;
            
            if (input <= kneePoint) {
                // Zona lineal (antes del knee)
                output = input + gainHFA;
            } else {
                // Zona de compresión (después del knee)
                const excessInput = input - kneePoint;
                const compressedGain = excessInput / ratio;
                output = kneePoint + gainHFA + compressedGain;
            }
            
            // Limitar output al rango visible
            output = Math.min(Math.max(output, 50), 120);
            
            points.push({ input, output });
        }

        // Dibujar curva suave
        points.forEach((point, index) => {
            const x = xScale(point.input);
            const y = yScale(point.output);
            
            if (index === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        });

        this.ctx.stroke();

        // Dibujar puntos de medición específicos
        this.drawMeasurementPoints(points, xScale, yScale);
    }

    /**
     * Dibujar puntos de medición específicos
     */
    drawMeasurementPoints(points, xScale, yScale) {
        // Puntos típicos de medición: 50, 65, 80 dB SPL
        const measurementInputs = [50, 65, 80];
        
        measurementInputs.forEach(inputLevel => {
            const point = points.find(p => Math.abs(p.input - inputLevel) < 1);
            if (point) {
                const x = xScale(point.input);
                const y = yScale(point.output);
                
                // Círculo de medición
                this.ctx.fillStyle = this.config.colors.inputOutput;
                this.ctx.beginPath();
                this.ctx.arc(x, y, 4, 0, 2 * Math.PI);
                this.ctx.fill();
                
                // Etiqueta con valores
                this.ctx.fillStyle = this.config.colors.text;
                this.ctx.font = '9px Arial';
                this.ctx.textAlign = 'center';
                this.ctx.fillText(`${Math.round(point.output)}`, x, y - 8);
            }
        });
    }

    /**
     * Dibujar punto de knee
     */
    drawKneePoint(data, xScale, yScale) {
        const kneePoint = data.knee_point;
        if (!kneePoint) return;

        const gainHFA = data.ganancia_hfa || 30;
        const kneeOutput = kneePoint + gainHFA;

        const x = xScale(kneePoint);
        const y = yScale(kneeOutput);

        // Círculo del knee point
        this.ctx.fillStyle = this.config.colors.kneePoint;
        this.ctx.strokeStyle = 'white';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(x, y, 6, 0, 2 * Math.PI);
        this.ctx.fill();
        this.ctx.stroke();

        // Etiqueta
        this.ctx.fillStyle = this.config.colors.kneePoint;
        this.ctx.font = 'bold 10px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`Knee: ${kneePoint} dB`, x + 10, y - 5);
    }

    /**
     * Dibujar leyenda
     */
    drawLegend(data) {
        const legendY = this.config.margin.top + 10;
        this.ctx.font = '10px Arial';
        this.ctx.textAlign = 'left';

        // Zona de compresión
        this.ctx.fillStyle = this.config.colors.compressionZone;
        this.ctx.fillRect(this.config.margin.left, legendY, 15, 8);
        this.ctx.strokeStyle = this.config.colors.threshold;
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(this.config.margin.left, legendY, 15, 8);
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.fillText('Zona de compresión', this.config.margin.left + 20, legendY + 6);

        // Curva I/O
        this.ctx.strokeStyle = this.config.colors.inputOutput;
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.moveTo(this.config.margin.left + 150, legendY + 4);
        this.ctx.lineTo(this.config.margin.left + 165, legendY + 4);
        this.ctx.stroke();
        this.ctx.fillText('Curva I/O medida', this.config.margin.left + 170, legendY + 6);

        // Línea lineal
        this.ctx.strokeStyle = this.config.colors.linear;
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([4, 2]);
        this.ctx.beginPath();
        this.ctx.moveTo(this.config.margin.left + 280, legendY + 4);
        this.ctx.lineTo(this.config.margin.left + 295, legendY + 4);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
        this.ctx.fillText('Lineal (1:1)', this.config.margin.left + 300, legendY + 6);

        // Knee point
        const kneeY = legendY + 15;
        this.ctx.fillStyle = this.config.colors.kneePoint;
        this.ctx.beginPath();
        this.ctx.arc(this.config.margin.left + 7, kneeY, 4, 0, 2 * Math.PI);
        this.ctx.fill();
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.fillText('Knee Point', this.config.margin.left + 20, kneeY + 3);
    }

    /**
     * Dibujar información de compresión
     */
    drawCompressionInfo(data) {
        const infoY = this.canvas.height - 50;
        this.ctx.font = '11px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillStyle = this.config.colors.text;

        let infoLines = [];

        // Ratio y knee point
        if (data.compression_ratio) {
            infoLines.push(`Ratio: ${data.compression_ratio}`);
        }
        if (data.knee_point) {
            infoLines.push(`Knee: ${data.knee_point} dB SPL`);
        }

        // Tiempos de ataque y release
        if (data.attack_time || data.release_time) {
            let timeText = 'Tiempos:';
            if (data.attack_time) timeText += ` Ataque=${data.attack_time}ms`;
            if (data.release_time) timeText += ` Release=${data.release_time}ms`;
            infoLines.push(timeText);
        }

        // Mostrar información
        infoLines.forEach((line, index) => {
            this.ctx.fillText(line, this.config.margin.left, infoY + (index * 15));
        });

        // Evaluación de la compresión
        this.drawCompressionEvaluation(data, infoY);
    }

    /**
     * Evaluar características de compresión
     */
    drawCompressionEvaluation(data, startY) {
        const evalX = this.canvas.width - 200;
        this.ctx.font = 'bold 10px Arial';
        this.ctx.textAlign = 'left';

        // Evaluar ratio
        const ratio = this.parseCompressionRatio(data.compression_ratio);
        if (ratio) {
            let ratioColor, ratioStatus;
            if (ratio <= 2) {
                ratioColor = '#28a745'; ratioStatus = 'SUAVE';
            } else if (ratio <= 4) {
                ratioColor = '#ffc107'; ratioStatus = 'MODERADO';
            } else {
                ratioColor = '#dc3545'; ratioStatus = 'AGRESIVO';
            }
            
            this.ctx.fillStyle = ratioColor;
            this.ctx.fillRect(evalX, startY, 12, 12);
            this.ctx.fillStyle = this.config.colors.text;
            this.ctx.fillText(`Compresión: ${ratioStatus}`, evalX + 18, startY + 9);
        }

        // Evaluar tiempos
        if (data.attack_time) {
            const attackColor = data.attack_time <= 10 ? '#28a745' : data.attack_time <= 20 ? '#ffc107' : '#dc3545';
            const attackStatus = data.attack_time <= 10 ? 'RÁPIDO' : data.attack_time <= 20 ? 'MEDIO' : 'LENTO';
            
            this.ctx.fillStyle = attackColor;
            this.ctx.fillRect(evalX, startY + 15, 12, 12);
            this.ctx.fillStyle = this.config.colors.text;
            this.ctx.fillText(`Ataque: ${attackStatus}`, evalX + 18, startY + 24);
        }

        // Calcular reducción de ganancia
        if (ratio && data.knee_point) {
            const reductionAt80 = this.calculateGainReduction(80, data.knee_point, ratio);
            this.ctx.fillStyle = this.config.colors.text;
            this.ctx.fillText(`Reducción @80dB: ${reductionAt80.toFixed(1)} dB`, evalX, startY + 35);
        }
    }

    /**
     * Calcular reducción de ganancia por compresión
     */
    calculateGainReduction(inputLevel, kneePoint, ratio) {
        if (inputLevel <= kneePoint) return 0;
        
        const excessInput = inputLevel - kneePoint;
        const reductionFactor = 1 - (1 / ratio);
        return excessInput * reductionFactor;
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
     * Exportar datos de compresión
     */
    exportCompressionData(data) {
        const ratio = this.parseCompressionRatio(data.compression_ratio) || 2;
        const kneePoint = data.knee_point || 55;
        
        return {
            ratio: ratio,
            kneePoint: kneePoint,
            gainReductionAt80: this.calculateGainReduction(80, kneePoint, ratio),
            compressionType: ratio <= 2 ? 'suave' : ratio <= 4 ? 'moderado' : 'agresivo',
            normativeData: this.normativeData
        };
    }
}

// Exponer globalmente
window.CompressionChartView = CompressionChartView;