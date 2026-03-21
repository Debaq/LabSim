/**
 * LogoaudioChartView - Vista previa de curvas logoaudiométricas
 * Componente reutilizable para renderizar gráficos de logoaudiometría
 */

class LogoaudioChartView {
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
                gridMajor: '#bbb',
                text: '#333'
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
        const xScale = (db) => this.config.margin.left + (db / 100) * plotWidth;
        const yScale = (percent) => this.config.margin.top + plotHeight - (percent / 100) * plotHeight;

        // Dibujar componentes
        this.drawGrid(plotWidth, plotHeight);
        this.drawAxes(plotWidth, plotHeight);
        this.drawData(data, xScale, yScale);
    }

    /**
     * Dibujar grilla del gráfico
     */
    drawGrid(width, height) {
        this.ctx.strokeStyle = this.config.colors.grid;
        this.ctx.lineWidth = 1;

        // Líneas verticales (intensidad - cada 10 dB)
        for (let db = 0; db <= 100; db += 10) {
            const x = this.config.margin.left + (db / 100) * width;

            this.ctx.strokeStyle = db % 20 === 0 ? this.config.colors.gridMajor : this.config.colors.grid;
            this.ctx.beginPath();
            this.ctx.moveTo(x, this.config.margin.top);
            this.ctx.lineTo(x, this.config.margin.top + height);
            this.ctx.stroke();
        }

        // Líneas horizontales (porcentaje - cada 10%)
        for (let percent = 0; percent <= 100; percent += 10) {
            const y = this.config.margin.top + height - (percent / 100) * height;

            this.ctx.strokeStyle = percent % 20 === 0 ? this.config.colors.gridMajor : this.config.colors.grid;
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

        // Etiquetas eje X (intensidad)
        for (let db = 0; db <= 100; db += 20) {
            const x = this.config.margin.left + (db / 100) * width;
            this.ctx.fillText(db.toString(), x - 8, this.config.margin.top + height + 15);
        }

        // Etiquetas eje Y (porcentaje)
        for (let percent = 0; percent <= 100; percent += 20) {
            const y = this.config.margin.top + height - (percent / 100) * height;
            this.ctx.fillText(percent + '%', this.config.margin.left - 25, y + 3);
        }

        // Títulos de ejes
        this.ctx.font = 'bold 12px Arial';
        this.ctx.fillText('Intensidad (dB HL)', this.config.margin.left + width/2 - 40, this.config.margin.top + height + 40);

        this.ctx.save();
        this.ctx.translate(15, this.config.margin.top + height/2);
        this.ctx.rotate(-Math.PI/2);
        this.ctx.fillText('Discriminación (%)', -40, 0);
        this.ctx.restore();
    }

    /**
     * Dibujar datos de las curvas
     */
    drawData(data, xScale, yScale) {
        const ears = [
            { key: 'oido_derecho', color: this.config.colors.od },
            { key: 'oido_izquierdo', color: this.config.colors.oi }
        ];

        ears.forEach(ear => {
            const points = this.extractPoints(data, ear.key);
            if (points.length === 0) return;

            // Ordenar puntos por intensidad
            points.sort((a, b) => a.intensity - b.intensity);

            // Convertir a coordenadas del canvas
            const canvasPoints = points.map(p => ({
                x: xScale(p.intensity),
                                                  y: yScale(p.discrimination),
                                                  ...p
            }));

            // Dibujar curva suave
            this.drawSmoothCurve(canvasPoints, ear.color);

            // Dibujar puntos
            this.drawPoints(canvasPoints, ear.color);
        });
    }

    /**
     * Extraer puntos de datos para un oído
     */
    extractPoints(data, earKey) {
        const points = [];

        // SDT (0%)
        const sdtValue = data.sdt_deteccion?.[earKey];
        if (this.isValidValue(sdtValue)) {
            points.push({
                intensity: sdtValue,
                discrimination: 0,
                label: 'SDT'
            });
        }

        // SRT (50%)
        const srtValue = data.srt_audibilidad?.[earKey];
        if (this.isValidValue(srtValue)) {
            points.push({
                intensity: srtValue,
                discrimination: 50,
                label: 'SRT'
            });
        }

        // UMD 1, 2, 3
        for (let i = 1; i <= 3; i++) {
            const umd = data.umd_inteligibilidad?.[earKey]?.[`umd${i}`];
            if (umd && this.isValidValue(umd.intensidad) && this.isValidValue(umd.porcentaje)) {
                points.push({
                    intensity: umd.intensidad,
                    discrimination: umd.porcentaje,
                    label: `UMD${i}`
                });
            }
        }

        return points;
    }

    /**
     * Verificar si un valor es válido
     */
    isValidValue(value) {
        return value !== null && value !== undefined && value !== '';
    }

    /**
     * Dibujar curva suave usando splines cúbicos
     */
    drawSmoothCurve(points, color) {
        if (points.length < 2) return;

        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();

        if (points.length === 2) {
            // Solo dos puntos: línea recta
            this.ctx.moveTo(points[0].x, points[0].y);
            this.ctx.lineTo(points[1].x, points[1].y);
        } else {
            // Múltiples puntos: curva suave
            this.drawCubicSpline(points);
        }

        this.ctx.stroke();
    }

    /**
     * Dibujar spline cúbico suave
     */
    drawCubicSpline(points) {
        this.ctx.moveTo(points[0].x, points[0].y);

        for (let i = 0; i < points.length - 1; i++) {
            const current = points[i];
            const next = points[i + 1];

            // Calcular puntos de control para curva de Bézier
            let cp1x = current.x + (next.x - current.x) * 0.3;
            let cp1y = current.y;
            let cp2x = next.x - (next.x - current.x) * 0.3;
            let cp2y = next.y;

            // Si hay puntos anteriores/siguientes, ajustar la curvatura
            if (i > 0) {
                const prev = points[i - 1];
                const slope = (next.y - prev.y) / (next.x - prev.x);
                cp1y = current.y + slope * (cp1x - current.x) * 0.3;
            }

            if (i < points.length - 2) {
                const nextNext = points[i + 2];
                const slope = (nextNext.y - current.y) / (nextNext.x - current.x);
                cp2y = next.y - slope * (next.x - cp2x) * 0.3;
            }

            this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, next.x, next.y);
        }
    }

    /**
     * Dibujar puntos de datos
     */
    drawPoints(points, color) {
        this.ctx.fillStyle = color;
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2;

        points.forEach(point => {
            this.ctx.beginPath();
            this.ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
            this.ctx.fill();
        });
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
}

// Exponer globalmente
window.LogoaudioChartView = LogoaudioChartView;
