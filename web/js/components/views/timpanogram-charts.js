/**
 * TimpanogramChartView - Vista previa de curvas timpanométricas
 * Componente reutilizable para renderizar gráficos de impedanciometría
 *
 * FUNCIONAMIENTO DEL GRADIENTE CLÍNICO:
 * - Gradiente = hp/ht (relación, no medida directa)
 * - hp: Distancia vertical desde compliance máxima hasta línea que intercepta curva en 2 puntos separados 100 daPa
 * - ht: Altura total de la curva (desde baseline hasta pico)
 * - Ancho: Diferencia en daPa entre puntos donde compliance = compliance_máxima / 2
 * - Las líneas punteadas marcan donde compliance = compliance_máxima / 2
 * - La línea continua marca el pico de compliance
 */

class TimpanogramChartView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.canvas = null;
        this.ctx = null;
        this.config = {
            margin: { top: 30, right: 40, bottom: 50, left: 60 },
            colors: {
                od: '#dc3545',
                oi: '#007bff',
                grid: '#ddd',
                gridMajor: '#333',
                text: '#333'
            },
            scales: {
                pressureMin: -200,
                pressureMax: 200,
                complianceMin: 0,
                complianceMax: 3
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
     * Renderizar gráfico con datos
     */
    render(data) {
        if (!this.init()) return;

        // Limpiar canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Configuración del área de dibujo
        const plotWidth = this.canvas.width - this.config.margin.left - this.config.margin.right;
        const plotHeight = this.canvas.height - this.config.margin.top - this.config.margin.bottom;

        // Funciones de escala
        const pressureScale = (pressure) =>
        this.config.margin.left + ((pressure - this.config.scales.pressureMin) /
        (this.config.scales.pressureMax - this.config.scales.pressureMin)) * plotWidth;

        const complianceScale = (compliance) =>
        this.config.margin.top + plotHeight - (compliance / this.config.scales.complianceMax) * plotHeight;

        // Dibujar componentes
        this.drawGrid(plotWidth, plotHeight);
        this.drawAxes(plotWidth, plotHeight);
        this.drawTimpanogramCurves(data, pressureScale, complianceScale);
    }

    /**
     * Dibujar grilla del gráfico
     */
    drawGrid(width, height) {
        // Líneas verticales (presión - cada 50 daPa)
        for (let pressure = this.config.scales.pressureMin; pressure <= this.config.scales.pressureMax; pressure += 50) {
            const x = this.config.margin.left + ((pressure - this.config.scales.pressureMin) /
            (this.config.scales.pressureMax - this.config.scales.pressureMin)) * width;

            // Línea más gruesa en 0 daPa
            if (pressure === 0) {
                this.ctx.strokeStyle = this.config.colors.gridMajor;
                this.ctx.lineWidth = 2;
            } else {
                this.ctx.strokeStyle = this.config.colors.grid;
                this.ctx.lineWidth = 1;
            }

            this.ctx.beginPath();
            this.ctx.moveTo(x, this.config.margin.top);
            this.ctx.lineTo(x, this.config.margin.top + height);
            this.ctx.stroke();
        }

        // Líneas horizontales (compliance - cada 0.5 ml)
        for (let compliance = this.config.scales.complianceMin; compliance <= this.config.scales.complianceMax; compliance += 0.5) {
            const y = this.config.margin.top + height - (compliance / this.config.scales.complianceMax) * height;

            this.ctx.strokeStyle = this.config.colors.grid;
            this.ctx.lineWidth = 1;

            this.ctx.beginPath();
            this.ctx.moveTo(this.config.margin.left, y);
            this.ctx.lineTo(this.config.margin.left + width, y);
            this.ctx.stroke();
        }
    }

    /**
     * Dibujar ejes y etiquetas
     */
    drawAxes(width, height) {
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.font = '11px Arial';

        // Etiquetas eje X (presión - cada 100 daPa)
        for (let pressure = this.config.scales.pressureMin; pressure <= this.config.scales.pressureMax; pressure += 100) {
            const x = this.config.margin.left + ((pressure - this.config.scales.pressureMin) /
            (this.config.scales.pressureMax - this.config.scales.pressureMin)) * width;

            this.ctx.textAlign = 'center';
            this.ctx.fillText(pressure.toString(), x, this.config.margin.top + height + 15);
        }

        // Etiquetas eje Y (compliance - cada 1.0 ml)
        for (let compliance = this.config.scales.complianceMin; compliance <= this.config.scales.complianceMax; compliance += 1.0) {
            const y = this.config.margin.top + height - (compliance / this.config.scales.complianceMax) * height;

            this.ctx.textAlign = 'right';
            this.ctx.fillText(compliance.toFixed(1), this.config.margin.left - 10, y + 4);
        }

        // Títulos de ejes
        this.ctx.font = 'bold 12px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('Presión (daPa)', this.config.margin.left + width/2, this.config.margin.top + height + 40);

        this.ctx.save();
        this.ctx.translate(20, this.config.margin.top + height/2);
        this.ctx.rotate(-Math.PI/2);
        this.ctx.fillText('Compliance (ml)', 0, 0);
        this.ctx.restore();
    }

    /**
     * Dibujar curvas timpanométricas
     */
    drawTimpanogramCurves(data, pressureScale, complianceScale) {
        const ears = [
            {
                data: data.timpanometria?.oido_derecho,
                color: this.config.colors.od,
                label: 'OD'
            },
            {
                data: data.timpanometria?.oido_izquierdo,
                color: this.config.colors.oi,
                label: 'OI'
            }
        ];

        ears.forEach(ear => {
            if (!this.hasValidTimpanogramData(ear.data)) return;

            const centerX = pressureScale(ear.data.presion);
            const peakY = complianceScale(ear.data.compliance_maxima);

            // Usar gradiente para calcular el ancho de la curva
            // El ancho se deriva del gradiente: gradiente más alto = curva más ancha
            const gradiente = ear.data.gradiente || 100;
            const anchoCalculado = this.calculateWidthFromGradient(gradiente);

            // Dibujar curva timpanométrica
            this.drawTimpanogramCurve(centerX, peakY, anchoCalculado, ear.color, pressureScale, complianceScale, ear.data);

            // Dibujar punto pico
            this.drawPeakPoint(centerX, peakY, ear.color);

            // Etiqueta del oído
            this.drawEarLabel(centerX, peakY, ear.label, ear.color);
        });
    }

    /**
     * Calcular ancho de curva a partir del gradiente
     * FUNCIONAMIENTO:
     * - Gradiente es hp/ht (relación)
     * - A mayor gradiente, curva más ancha
     * - Gradiente típico: 0.1-0.8 (curvas estrechas a anchas)
     * - Convertimos a ancho en daPa para generar la curva
     */
    calculateWidthFromGradient(gradiente) {
        // Mapear gradiente (0-300 daPa típico) a ancho de curva
        // Gradiente menor = curva más estrecha, gradiente mayor = curva más ancha
        const minWidth = 40;  // Ancho mínimo en daPa
        const maxWidth = 160; // Ancho máximo en daPa
        const normalizedGradient = Math.min(gradiente, 300) / 300; // Normalizar 0-1

        return minWidth + (maxWidth - minWidth) * normalizedGradient;
    }

    /**
     * Verificar si los datos del timpanograma son válidos
     */
    hasValidTimpanogramData(earData) {
        return earData &&
        earData.compliance_maxima !== null &&
        earData.compliance_maxima !== undefined &&
        earData.presion !== null &&
        earData.presion !== undefined &&
        !isNaN(earData.compliance_maxima) &&
        !isNaN(earData.presion);
    }

    /**
     * Dibujar curva timpanométrica individual
     *
     * ALGORITMO DE LA CURVA:
     * 1. Se dibuja siempre de -200 a +200 daPa
     * 2. El "ancho" determina dónde la compliance = compliance_máxima/2
     * 3. La curva tiene forma exponencial para simular timpanograma real
     * 4. Baseline fijo en 0.1 ml
     * 5. El pico es puntiagudo (no redondeado)
     */
    drawTimpanogramCurve(centerX, peakY, ancho, color, pressureScale, complianceScale, earData) {
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();

        // Parámetros de la curva
        const startPressure = -200;
        const endPressure = 200;
        const baselineCompliance = 0.1;
        const centerPressure = this.invertPressureScale(centerX, pressureScale);
        const peakCompliance = this.invertComplianceScale(peakY, complianceScale);

        // Compliance a la mitad (donde se mide el ancho)
        const halfCompliance = (peakCompliance + baselineCompliance) / 2;

        // Generar puntos de la curva
        const numPoints = 100;
        let firstPoint = true;

        for (let i = 0; i <= numPoints; i++) {
            const pressure = startPressure + (endPressure - startPressure) * (i / numPoints);
            const x = pressureScale(pressure);

            // Calcular compliance usando curva exponencial
            const distanceFromCenter = Math.abs(pressure - centerPressure);

            // Factor de decaimiento exponencial basado en el ancho
            // En el ancho/2, la compliance debe ser halfCompliance
            const decayFactor = Math.exp(-Math.pow(distanceFromCenter / (ancho/2), 2.5));

            const compliance = baselineCompliance + (peakCompliance - baselineCompliance) * decayFactor;
            const y = complianceScale(compliance);

            if (firstPoint) {
                this.ctx.moveTo(x, y);
                firstPoint = false;
            } else {
                this.ctx.lineTo(x, y);
            }
        }

        this.ctx.stroke();

        // Dibujar líneas de referencia
        this.drawGradientReferenceLines(centerX, centerPressure, ancho, pressureScale, complianceScale, color, earData);
    }

    /**
     * Dibujar líneas de referencia del gradiente
     *
     * LÍNEAS DE REFERENCIA:
     * - Línea continua: En el pico (presión central)
     * - Líneas punteadas: Donde compliance = compliance_máxima/2
     * - Estas marcan el "ancho" del timpanograma clínicamente
     */
    drawGradientReferenceLines(centerX, centerPressure, ancho, pressureScale, complianceScale, color, earData) {
        const margin = this.config.margin;
        const plotHeight = this.canvas.height - margin.top - margin.bottom;

        // Línea continua en el pico (centro)
        this.ctx.setLineDash([]);
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 1;
        this.ctx.globalAlpha = 0.7;

        this.ctx.beginPath();
        this.ctx.moveTo(centerX, margin.top);
        this.ctx.lineTo(centerX, margin.top + plotHeight);
        this.ctx.stroke();

        // Líneas punteadas donde compliance = compliance_máxima/2
        // Estas están aproximadamente a ancho/2 del centro
        this.ctx.setLineDash([3, 3]);
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 1;
        this.ctx.globalAlpha = 0.5;

        // Línea izquierda (ancho/2 hacia la izquierda del pico)
        const leftWidthX = pressureScale(centerPressure - ancho/2);
        this.ctx.beginPath();
        this.ctx.moveTo(leftWidthX, margin.top);
        this.ctx.lineTo(leftWidthX, margin.top + plotHeight);
        this.ctx.stroke();

        // Línea derecha (ancho/2 hacia la derecha del pico)
        const rightWidthX = pressureScale(centerPressure + ancho/2);
        this.ctx.beginPath();
        this.ctx.moveTo(rightWidthX, margin.top);
        this.ctx.lineTo(rightWidthX, margin.top + plotHeight);
        this.ctx.stroke();

        // Restaurar configuración
        this.ctx.setLineDash([]);
        this.ctx.globalAlpha = 1.0;
    }

    /**
     * Convertir coordenada X a presión
     */
    invertPressureScale(x, pressureScale) {
        const plotWidth = this.canvas.width - this.config.margin.left - this.config.margin.right;
        const ratio = (x - this.config.margin.left) / plotWidth;
        return this.config.scales.pressureMin + ratio * (this.config.scales.pressureMax - this.config.scales.pressureMin);
    }

    /**
     * Convertir coordenada Y a compliance
     */
    invertComplianceScale(y, complianceScale) {
        const plotHeight = this.canvas.height - this.config.margin.top - this.config.margin.bottom;
        const ratio = (this.config.margin.top + plotHeight - y) / plotHeight;
        return ratio * this.config.scales.complianceMax;
    }

    /**
     * Dibujar punto pico
     */
    drawPeakPoint(x, y, color) {
        this.ctx.fillStyle = color;
        this.ctx.beginPath();
        this.ctx.arc(x, y, 4, 0, 2 * Math.PI);
        this.ctx.fill();

        // Borde blanco para mejor visibilidad
        this.ctx.strokeStyle = 'white';
        this.ctx.lineWidth = 1;
        this.ctx.stroke();
    }

    /**
     * Dibujar etiqueta del oído
     */
    drawEarLabel(x, y, label, color) {
        this.ctx.fillStyle = color;
        this.ctx.font = 'bold 12px Arial';
        this.ctx.textAlign = 'left';

        // Posicionar etiqueta offset del punto
        const offsetX = 10;
        const offsetY = -10;

        this.ctx.fillText(label, x + offsetX, y + offsetY);
    }

    /**
     * Obtener tipo de timpanograma basado en los datos
     */
    getTimpanogramType(earData) {
        if (!this.hasValidTimpanogramData(earData)) return null;

        const compliance = parseFloat(earData.compliance_maxima);
        const presion = parseFloat(earData.presion);

        // Clasificación según criterios clínicos estándar
        if (compliance >= 0.3 && compliance <= 1.6 && presion >= -100 && presion <= 100) {
            return { type: 'A', description: 'Normal' };
        }

        if (compliance < 0.3) {
            return { type: 'B', description: 'Plano' };
        }

        if (presion < -100) {
            return { type: 'C', description: 'Presión negativa' };
        }

        if (compliance < 0.3 && presion >= -100 && presion <= 100) {
            return { type: 'As', description: 'Rígido' };
        }

        if (compliance > 1.6 && presion >= -100 && presion <= 100) {
            return { type: 'Ad', description: 'Hipermóvil' };
        }

        return { type: 'Atípico', description: 'Fuera de parámetros normales' };
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
            this.canvas.style.width = '100%';
            this.canvas.style.height = 'auto';
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
     * Exportar canvas como imagen
     */
    exportAsImage(format = 'png') {
        if (this.canvas) {
            return this.canvas.toDataURL(`image/${format}`);
        }
        return null;
    }

    /**
     * Configurar opciones del gráfico
     */
    configure(options) {
        if (options.colors) {
            this.config.colors = { ...this.config.colors, ...options.colors };
        }
        if (options.scales) {
            this.config.scales = { ...this.config.scales, ...options.scales };
        }
        if (options.margin) {
            this.config.margin = { ...this.config.margin, ...options.margin };
        }
    }
}

// Exponer globalmente
window.TimpanogramChartView = TimpanogramChartView;
