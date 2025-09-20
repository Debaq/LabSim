/**
 * DPOAEClinicalChartView - Vista de DPOAE Clínicas
 * Gráfico de amplitud vs frecuencia con áreas de normalidad
 */

class DPOAEClinicalChartView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.canvas = null;
        this.ctx = null;
        this.config = {
            margin: { top: 60, right: 40, bottom: 50, left: 60 },
            colors: {
                od: '#dc3545',
                oi: '#007bff',
                grid: '#e0e0e0',
                gridMajor: '#ccc',
                text: '#333',
                normalArea: 'rgba(40, 167, 69, 0.15)',
                noiseLine: '#999'
            }
        };

        // Datos normativos del DP-Gram
        this.normativeData = {
            1.0: { noise: -15, p5: 5, p95: 22 },
            1.5: { noise: -16, p5: 4, p95: 21 },
            2.0: { noise: -17, p5: 3, p95: 18 },
            3.0: { noise: -18, p5: 1, p95: 15 },
            4.0: { noise: -18, p5: -1, p95: 13 },
            5.0: { noise: -19, p5: -3, p95: 12 },
            6.0: { noise: -20, p5: -4, p95: 11 },
            7.0: { noise: -20, p5: -3, p95: 13 },
            8.0: { noise: -20, p5: -2, p95: 14 }
        };

        // Frecuencias para el eje X (logarítmico)
        this.frequencies = [1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0];
        this.testFrequencies = [1.0, 1.5, 2.0, 3.0, 4.0, 6.0]; // Solo estas se evalúan clínicamente
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
        const xScale = (freqIndex) => this.config.margin.left + (freqIndex / (this.frequencies.length - 1)) * plotWidth;
        const yScale = (amplitude) => this.config.margin.top + plotHeight - ((amplitude + 30) / 60) * plotHeight;

        // Dibujar componentes
        this.drawGrid(plotWidth, plotHeight, xScale, yScale);
        this.drawNormalityAreas(xScale, yScale);
        this.drawNoiseLine(xScale, yScale);
        this.drawAxes(plotWidth, plotHeight);
        this.drawData(data, xScale, yScale);
        this.drawLegend();
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
            
            // Líneas más gruesas para frecuencias evaluadas clínicamente
            if (this.testFrequencies.includes(freq)) {
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

        // Líneas horizontales (amplitud - cada 5 dB)
        for (let db = -30; db <= 30; db += 5) {
            const y = yScale(db);
            
            // Línea más gruesa en 0 dB
            if (db === 0) {
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
     * Dibujar áreas de normalidad (P5-P95)
     */
    drawNormalityAreas(xScale, yScale) {
        this.ctx.fillStyle = this.config.colors.normalArea;
        this.ctx.strokeStyle = 'rgba(40, 167, 69, 0.5)';
        this.ctx.lineWidth = 1;

        // Crear path para área de normalidad
        this.ctx.beginPath();
        
        // Línea superior (P95)
        this.frequencies.forEach((freq, index) => {
            const normData = this.normativeData[freq];
            if (normData) {
                const x = xScale(index);
                const y = yScale(normData.p95);
                
                if (index === 0) {
                    this.ctx.moveTo(x, y);
                } else {
                    this.ctx.lineTo(x, y);
                }
            }
        });
        
        // Línea inferior (P5) - en reversa
        for (let i = this.frequencies.length - 1; i >= 0; i--) {
            const freq = this.frequencies[i];
            const normData = this.normativeData[freq];
            if (normData) {
                const x = xScale(i);
                const y = yScale(normData.p5);
                this.ctx.lineTo(x, y);
            }
        }
        
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.stroke();
    }

    /**
     * Dibujar línea de ruido
     */
    drawNoiseLine(xScale, yScale) {
        this.ctx.strokeStyle = this.config.colors.noiseLine;
        this.ctx.lineWidth = 1;
        this.ctx.setLineDash([3, 3]);
        
        this.ctx.beginPath();
        this.frequencies.forEach((freq, index) => {
            const normData = this.normativeData[freq];
            if (normData) {
                const x = xScale(index);
                const y = yScale(normData.noise);
                
                if (index === 0) {
                    this.ctx.moveTo(x, y);
                } else {
                    this.ctx.lineTo(x, y);
                }
            }
        });
        this.ctx.stroke();
        this.ctx.setLineDash([]);
    }

    /**
     * Dibujar ejes y etiquetas
     */
    drawAxes(width, height) {
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.font = '11px Arial';
        this.ctx.textAlign = 'center';

        // Etiquetas eje X (frecuencias)
        this.frequencies.forEach((freq, index) => {
            const x = this.config.margin.left + (index / (this.frequencies.length - 1)) * width;
            const label = freq >= 1 ? `${freq}k` : `${freq * 1000}`;
            
            // Destacar frecuencias evaluadas clínicamente
            if (this.testFrequencies.includes(freq)) {
                this.ctx.font = 'bold 11px Arial';
                this.ctx.fillStyle = '#333';
            } else {
                this.ctx.font = '10px Arial';
                this.ctx.fillStyle = '#666';
            }
            
            this.ctx.fillText(label, x, this.config.margin.top + height + 15);
        });

        // Etiquetas eje Y (amplitud)
        this.ctx.textAlign = 'right';
        this.ctx.font = '11px Arial';
        this.ctx.fillStyle = this.config.colors.text;
        
        for (let db = -30; db <= 30; db += 10) {
            const y = this.config.margin.top + height - ((db + 30) / 60) * height;
            this.ctx.fillText(`${db}`, this.config.margin.left - 10, y + 4);
        }

        // Títulos de ejes
        this.ctx.textAlign = 'center';
        this.ctx.font = 'bold 12px Arial';
        this.ctx.fillText('Frecuencia (Hz)', this.config.margin.left + width/2, this.config.margin.top + height + 35);

        this.ctx.save();
        this.ctx.translate(20, this.config.margin.top + height/2);
        this.ctx.rotate(-Math.PI/2);
        this.ctx.fillText('Amplitud DPOAE (dB SPL)', 0, 0);
        this.ctx.restore();
    }

    /**
     * Dibujar datos de DPOAE
     */
    drawData(data, xScale, yScale) {
        const ears = [
            { key: 'oido_derecho', color: this.config.colors.od, label: 'OD' },
            { key: 'oido_izquierdo', color: this.config.colors.oi, label: 'OI' }
        ];

        ears.forEach(ear => {
            const earData = data.producto_distorsion_clinicas?.[ear.key];
            if (!earData) return;

            const points = [];
            const presentPoints = [];
            const absentPoints = [];

            // Recopilar puntos de datos
            this.testFrequencies.forEach(freq => {
                const freqIndex = this.frequencies.indexOf(freq);
                const measurement = earData[freq.toString()];
                
                if (measurement && measurement.amplitud !== null && measurement.amplitud !== undefined) {
                    const x = xScale(freqIndex);
                    const y = yScale(measurement.amplitud);
                    const point = { x, y, freq, amp: measurement.amplitud, resp: measurement.respuesta };
                    
                    points.push(point);
                    
                    if (measurement.respuesta === 'presente') {
                        presentPoints.push(point);
                    } else if (measurement.respuesta === 'ausente') {
                        absentPoints.push(point);
                    }
                }
            });

            // Dibujar línea conectora solo para respuestas presentes
            if (presentPoints.length > 1) {
                this.ctx.strokeStyle = ear.color;
                this.ctx.lineWidth = 2;
                this.ctx.setLineDash([]);
                
                this.ctx.beginPath();
                presentPoints.forEach((point, index) => {
                    if (index === 0) {
                        this.ctx.moveTo(point.x, point.y);
                    } else {
                        this.ctx.lineTo(point.x, point.y);
                    }
                });
                this.ctx.stroke();
            }

            // Dibujar símbolos para respuestas presentes
            presentPoints.forEach(point => {
                this.drawSymbol(point.x, point.y, 'circle', ear.color, true);
            });

            // Dibujar símbolos para respuestas ausentes
            absentPoints.forEach(point => {
                this.drawSymbol(point.x, point.y, 'x', ear.color, false);
            });
        });
    }

    /**
     * Dibujar símbolos de datos
     */
    drawSymbol(x, y, symbol, color, filled) {
        this.ctx.fillStyle = color;
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2;

        switch (symbol) {
            case 'circle':
                this.ctx.beginPath();
                this.ctx.arc(x, y, 4, 0, 2 * Math.PI);
                if (filled) {
                    this.ctx.fill();
                } else {
                    this.ctx.stroke();
                }
                break;
            case 'x':
                this.ctx.beginPath();
                this.ctx.moveTo(x - 4, y - 4);
                this.ctx.lineTo(x + 4, y + 4);
                this.ctx.moveTo(x + 4, y - 4);
                this.ctx.lineTo(x - 4, y + 4);
                this.ctx.stroke();
                break;
        }
    }

    /**
     * Dibujar leyenda
     */
    drawLegend() {
        const legendY = 5;
        this.ctx.font = '10px Arial';
        this.ctx.textAlign = 'left';

        // Área de normalidad
        this.ctx.fillStyle = this.config.colors.normalArea;
        this.ctx.fillRect(this.config.margin.left, legendY, 15, 8);
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.fillText('Área normal (P5-P95)', this.config.margin.left + 20, legendY + 6);

        // Línea de ruido
        this.ctx.strokeStyle = this.config.colors.noiseLine;
        this.ctx.setLineDash([3, 3]);
        this.ctx.beginPath();
        this.ctx.moveTo(this.config.margin.left + 150, legendY + 4);
        this.ctx.lineTo(this.config.margin.left + 165, legendY + 4);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
        this.ctx.fillText('Nivel de ruido', this.config.margin.left + 170, legendY + 6);

        // Símbolos de oídos
        const symbolY = legendY + 15;
        
        // OD
        this.drawSymbol(this.config.margin.left + 7, symbolY, 'circle', this.config.colors.od, true);
        this.ctx.fillStyle = this.config.colors.text;
        this.ctx.fillText('OD Presente', this.config.margin.left + 20, symbolY + 3);

        // OI
        this.drawSymbol(this.config.margin.left + 100, symbolY, 'circle', this.config.colors.oi, true);
        this.ctx.fillText('OI Presente', this.config.margin.left + 113, symbolY + 3);

        // Ausente
        this.drawSymbol(this.config.margin.left + 200, symbolY, 'x', '#666', false);
        this.ctx.fillText('Ausente', this.config.margin.left + 213, symbolY + 3);
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
window.DPOAEClinicalChartView = DPOAEClinicalChartView;
