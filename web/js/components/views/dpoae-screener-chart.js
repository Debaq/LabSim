/**
 * DPOAEScreenerChartView - Vista de DPOAE Screener
 * Barras por frecuencia (OD y OI). Cada barra tiene dos partes:
 *  - Base: nivel de ruido (estimado si no está disponible)
 *  - Tope: nivel de señal (amplitud)
 * Indicadores:
 *  - ✔️ verde si PASA
 *  - ❌ rojo si NO PASA
 *  - ⚠️ amarillo si PENDIENTE
 */

class DPOAEScreenerChartView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.canvas = null;
        this.ctx = null;

        this.config = {
            margin: { top: 34, right: 24, bottom: 48, left: 54 },
            colors: {
                od: '#dc3545',       // rojo
                oi: '#007bff',       // azul
                odLight: 'rgba(220,53,69,0.35)',
                oiLight: 'rgba(0,123,255,0.35)',
                grid: '#e0e0e0',
                gridMajor: '#c9c9c9',
                text: '#333',
                axis: '#555',
                limit: '#6f42c1',    // línea de límite (-5 dB)
                pass: '#28a745',     // tick
                fail: '#dc3545',     // X
                pending: '#ffad00',  // ⚠️
                panelBorder: '#e5e7eb'
            },
            yMin: -30,
            yMax: 10,
            frequencies: [1000, 1500, 2000, 3000, 4000, 6000],
            passThreshold: -5,
            bar: {
                groupGap: 22,
                pairGap: 6,
                width: 16
            }
        };
    }

    init() {
        this.canvas = document.getElementById(this.canvasId);
        if (!this.canvas) {
            console.warn(`Canvas ${this.canvasId} no encontrado`);
            return false;
        }
        this.ctx = this.canvas.getContext('2d');
        return true;
    }

    render(data) {
        if (!this.init()) return;

        const { ctx, canvas } = this;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const W = canvas.width;
        const H = canvas.height;
        const { margin, yMin, yMax } = this.config;

        const innerW = W - margin.left - margin.right;
        const innerH = H - margin.top - margin.bottom;

        const yScale = (db) => margin.top + innerH - ((db - yMin) / (yMax - yMin)) * innerH;
        const xScaleGroupCenter = this.getGroupXCenters(margin.left, innerW);

        this.strokeRect(margin.left, margin.top, innerW, innerH, this.config.colors.panelBorder);
        this.drawGrid(margin.left, margin.top, innerW, innerH, yScale);
        this.drawLimitLine(margin.left, innerW, yScale);

        const screener = data?.producto_distorsion_screener || {};
        const odData = screener.oido_derecho || {};
        const oiData = screener.oido_izquierdo || {};

        this.config.frequencies.forEach((freq, idx) => {
            const xCenter = xScaleGroupCenter[idx];

            this.drawBarForEar(
                odData[String(freq)],
                               xCenter - (this.config.bar.width / 2) - (this.config.bar.pairGap / 2),
                               this.config.colors.od,
                               this.config.colors.odLight,
                               yScale
            );

            this.drawBarForEar(
                oiData[String(freq)],
                               xCenter + (this.config.bar.width / 2) + (this.config.bar.pairGap / 2) - this.config.bar.width,
                               this.config.colors.oi,
                               this.config.colors.oiLight,
                               yScale
            );

            this.drawFreqLabel(freq, xCenter, margin.top + innerH + 16);
        });

        // Leyenda en dos filas
        this.drawLegend(margin.left, margin.top - 18);
    }

    // =================== DIBUJO BASE ===================

    drawGrid(x, y, w, h, yScale) {
        const { ctx } = this;
        const { grid, gridMajor, text } = this.config.colors;

        for (let db = this.config.yMin; db <= this.config.yMax; db += 5) {
            const yy = yScale(db);
            ctx.strokeStyle = (db % 10 === 0 || db === 0) ? gridMajor : grid;
            ctx.lineWidth = (db === 0) ? 1.8 : 1;
            ctx.beginPath();
            ctx.moveTo(x, yy);
            ctx.lineTo(x + w, yy);
            ctx.stroke();

            if (db % 10 === 0) {
                ctx.fillStyle = text;
                ctx.font = '10px Arial';
                ctx.textAlign = 'right';
                ctx.fillText(`${db}`, x - 6, yy + 3);
            }
        }
    }

    drawLimitLine(x, w, yScale) {
        const { ctx } = this;
        const y = yScale(this.config.passThreshold);
        ctx.save();
        ctx.strokeStyle = this.config.colors.limit;
        ctx.setLineDash([5, 3]);
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + w, y);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = this.config.colors.limit;
        ctx.font = '10px Arial';
        ctx.textAlign = 'left';
        ctx.fillText(`Límite ${this.config.passThreshold} dB SPL`, x + 6, y - 6);
        ctx.restore();
    }

    strokeRect(x, y, w, h, color) {
        const { ctx } = this;
        ctx.save();
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, w, h);
        ctx.restore();
    }

    getGroupXCenters(x0, innerW) {
        const n = this.config.frequencies.length;
        const totalGap = (n - 1) * this.config.bar.groupGap;
        const barsArea = innerW - totalGap;
        const groupWidth = (this.config.bar.width * 2) + this.config.bar.pairGap;

        const scale = Math.min(1, barsArea / (groupWidth * n));
        const effectiveGroupWidth = groupWidth * scale;

        const centers = [];
        let x = x0 + (effectiveGroupWidth / 2);
        for (let i = 0; i < n; i++) {
            centers.push(x);
            x += effectiveGroupWidth + this.config.bar.groupGap;
        }
        return centers;
    }

    drawFreqLabel(freq, x, y) {
        const { ctx } = this;
        ctx.save();
        ctx.fillStyle = this.config.colors.axis;
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(`${freq}`, x, y);
        ctx.restore();
    }

    // =================== BARRAS ===================

    drawBarForEar(entry, xLeft, colorSolid, colorLight, yScale) {
        const { ctx } = this;
        const bw = this.config.bar.width;
        const yMinPx = yScale(this.config.yMin);

        const amp = (entry && typeof entry.amplitud === 'number') ? entry.amplitud : null;
        const status = (entry && entry.resultado) ? String(entry.resultado).toLowerCase() : 'pendiente';

        let noiseLevel;
        if (status === 'pasa' && amp !== null) {
            noiseLevel = Math.min(amp - 10, -15);
        } else if (status === 'no-pasa' && amp !== null) {
            noiseLevel = amp - 3;
        } else {
            noiseLevel = -20;
        }
        noiseLevel = Math.max(this.config.yMin, Math.min(this.config.yMax, noiseLevel));
        const signalLevel = (amp !== null) ? Math.max(this.config.yMin, Math.min(this.config.yMax, amp)) : -25;

        const yNoise = yScale(noiseLevel);
        const ySignal = yScale(signalLevel);

        ctx.save();
        ctx.fillStyle = colorLight;
        const noiseTop = Math.min(yNoise, yMinPx);
        ctx.fillRect(xLeft, noiseTop, bw, yMinPx - noiseTop);

        ctx.fillStyle = colorSolid;
        const topY = Math.min(ySignal, yNoise);
        const bottomY = Math.max(ySignal, yNoise);
        const h = Math.max(2, bottomY - topY);
        ctx.fillRect(xLeft, topY, bw, h);
        ctx.restore();

        const cx = xLeft + bw / 2;
        const topOfBarY = Math.min(ySignal, yNoise) - 6;
        this.drawStatusIcon(status, cx, topOfBarY);
    }

    drawStatusIcon(status, x, y) {
        const { ctx } = this;

        if (status === 'pasa') {
            ctx.save();
            ctx.strokeStyle = this.config.colors.pass;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x - 6, y);
            ctx.lineTo(x - 1, y + 6);
            ctx.lineTo(x + 7, y - 6);
            ctx.stroke();
            ctx.restore();
        } else if (status === 'no-pasa') {
            ctx.save();
            ctx.strokeStyle = this.config.colors.fail;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x - 6, y - 6);
            ctx.lineTo(x + 6, y + 6);
            ctx.moveTo(x + 6, y - 6);
            ctx.lineTo(x - 6, y + 6);
            ctx.stroke();
            ctx.restore();
        } else {
            ctx.save();
            ctx.fillStyle = this.config.colors.pending;
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fill();
            ctx.restore();
        }
    }

    // =================== LEYENDA ===================

    drawLegend(x, y) {
        const { ctx } = this;
        ctx.save();
        ctx.font = '10px Arial';
        ctx.textAlign = 'left';

        // Línea 1: OD / OI
        let off = 0;
        ctx.fillStyle = this.config.colors.odLight;
        ctx.fillRect(x + off, y, 12, 6);
        ctx.fillStyle = this.config.colors.od;
        ctx.fillRect(x + off, y - 6, 12, 4);
        ctx.fillStyle = this.config.colors.text;
        ctx.fillText('OD: Señal + Ruido', x + off + 18, y + 4);
        off += 140;

        ctx.fillStyle = this.config.colors.oiLight;
        ctx.fillRect(x + off, y, 12, 6);
        ctx.fillStyle = this.config.colors.oi;
        ctx.fillRect(x + off, y - 6, 12, 4);
        ctx.fillStyle = this.config.colors.text;
        ctx.fillText('OI: Señal + Ruido', x + off + 18, y + 4);

        // Línea 2: símbolos de estado
        let y2 = y + 16;
        off = 0;

        ctx.strokeStyle = this.config.colors.pass;
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(x + off, y2 - 4); ctx.lineTo(x + off + 5, y2 + 2); ctx.lineTo(x + off + 12, y2 - 8); ctx.stroke();
        ctx.fillStyle = this.config.colors.text; ctx.fillText('PASA', x + off + 18, y2);
        off += 70;

        ctx.strokeStyle = this.config.colors.fail;
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(x + off, y2 - 8); ctx.lineTo(x + off + 12, y2 + 4); ctx.moveTo(x + off + 12, y2 - 8); ctx.lineTo(x + off, y2 + 4); ctx.stroke();
        ctx.fillStyle = this.config.colors.text; ctx.fillText('NO PASA', x + off + 18, y2);
        off += 90;

        ctx.fillStyle = this.config.colors.pending;
        ctx.beginPath(); ctx.arc(x + off + 4, y2 - 2, 4, 0, 2 * Math.PI); ctx.fill();
        ctx.fillStyle = this.config.colors.text; ctx.fillText('Pendiente', x + off + 18, y2);

        ctx.restore();
    }
}

// Exponer globalmente
window.DPOAEScreenerChartView = DPOAEScreenerChartView;
