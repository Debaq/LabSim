/**
 * TEOAEScreenerChartView - Vista de TEOAE Screener
 * Barras por frecuencia (OD y OI). Cada barra = SNR (dB).
 * Indicadores:
 *  - ✔️ verde si PASA (SNR ≥ 6 dB y resp = 'presente')
 *  - ❌ rojo si NO PASA
 *  - ⚠️ amarillo si PENDIENTE (sin datos)
 *
 * Lee de: data.transientes_screener.{oido_derecho|oido_izquierdo}[freq] = { resultado, snr }
 */

class TEOAEScreenerChartView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.canvas = null;
        this.ctx = null;

        this.config = {
            margin: { top: 34, right: 24, bottom: 48, left: 54 },
            colors: {
                od: '#dc3545',       // rojo
                oi: '#007bff',       // azul
                odFill: 'rgba(220,53,69,0.85)',
                oiFill: 'rgba(0,123,255,0.85)',
                grid: '#e0e0e0',
                gridMajor: '#c9c9c9',
                text: '#333',
                axis: '#555',
                limit: '#28a745',    // línea de corte (6 dB)
                borderline: '#ffc107', // línea de 3 dB (opcional)
                pass: '#28a745',     // tick
                fail: '#dc3545',     // X
                pending: '#ffad00',  // ⚠️
                panelBorder: '#e5e7eb'
            },
            // Rango SNR habitual
            yMin: 0,
            yMax: 30,
            // Frecuencias clínicas del screener (coinciden con OaeModule)
            frequencies: [1000, 1500, 2000, 3000, 4000],
            // Umbrales clínicos
            passThreshold: 6,  // PASA si SNR ≥ 6
            borderlineThreshold: 3, // informativo (no cambia el resultado del screener)
            // Geometría
            bar: {
                groupGap: 26, // espacio entre grupos de frecuencias
                pairGap: 8,   // espacio entre OD y OI
                width: 16     // ancho de cada barra
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
        const xCenters = this.getGroupXCenters(margin.left, innerW);

        // Marco
        this.strokeRect(margin.left, margin.top, innerW, innerH, this.config.colors.panelBorder);

        // Grilla y ejes
        this.drawGrid(margin.left, margin.top, innerW, innerH, yScale);

        // Líneas de umbral
        this.drawThresholdLines(margin.left, innerW, yScale);

        // Datos del screener
        const scr = data?.transientes_screener || {};
        const od = scr.oido_derecho || {};
        const oi = scr.oido_izquierdo || {};

        // Barras por frecuencia
        this.config.frequencies.forEach((freq, i) => {
            const xC = xCenters[i];

            // OD
            this.drawBar(
                od[String(freq)],
                xC - (this.config.bar.width / 2) - (this.config.bar.pairGap / 2),
                this.config.colors.odFill,
                yScale
            );

            // OI
            this.drawBar(
                oi[String(freq)],
                xC + (this.config.bar.width / 2) + (this.config.bar.pairGap / 2) - this.config.bar.width,
                this.config.colors.oiFill,
                yScale
            );

            // Etiqueta de frecuencia
            this.drawFreqLabel(freq, xC, margin.top + innerH + 16);
        });

        // Leyenda (dos líneas)
        this.drawLegend(margin.left, margin.top - 18);
    }

    // =================== Dibujo base ===================

    drawGrid(x, y, w, h, yScale) {
        const { ctx } = this;
        const { grid, gridMajor, text } = this.config.colors;

        for (let db = this.config.yMin; db <= this.config.yMax; db += 2) {
            const yy = yScale(db);
            const isMajor = db % 10 === 0 || db === 0;
            ctx.strokeStyle = isMajor ? gridMajor : grid;
            ctx.lineWidth = isMajor ? 1.5 : 1;
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

    drawThresholdLines(x, w, yScale) {
        const { ctx } = this;

        // Línea de PASA (6 dB)
        const yPass = yScale(this.config.passThreshold);
        ctx.save();
        ctx.strokeStyle = this.config.colors.limit;
        ctx.setLineDash([6, 3]);
        ctx.lineWidth = 1.8;
        ctx.beginPath(); ctx.moveTo(x, yPass); ctx.lineTo(x + w, yPass); ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = this.config.colors.limit;
        ctx.font = '10px Arial';
        ctx.textAlign = 'left';
        ctx.fillText(`Corte PASA ${this.config.passThreshold} dB`, x + 6, yPass - 6);
        ctx.restore();

        // Línea de 3 dB (informativa)
        const yBorder = yScale(this.config.borderlineThreshold);
        ctx.save();
        ctx.strokeStyle = this.config.colors.borderline;
        ctx.setLineDash([4, 4]);
        ctx.lineWidth = 1.2;
        ctx.beginPath(); ctx.moveTo(x, yBorder); ctx.lineTo(x + w, yBorder); ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = this.config.colors.borderline;
        ctx.font = '10px Arial';
        ctx.textAlign = 'left';
        ctx.fillText(`Zona límite ${this.config.borderlineThreshold} dB`, x + 6, yBorder - 6);
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

    // =================== Barras por SNR ===================

    drawBar(entry, xLeft, fillColor, yScale) {
        const { ctx } = this;
        const bw = this.config.bar.width;
        const yZero = yScale(0);

        const snr = (entry && typeof entry.snr === 'number') ? entry.snr : null;
        const status = (entry && entry.resultado) ? String(entry.resultado).toLowerCase() : 'pendiente';

        // Altura de barra
        const snrClamped = (snr !== null) ? Math.max(this.config.yMin, Math.min(this.config.yMax, snr)) : 0;
        const yTop = yScale(snrClamped);

        // Barra (desde 0 dB hasta SNR)
        ctx.save();
        ctx.fillStyle = fillColor;
        const top = Math.min(yTop, yZero);
        const h = Math.max(2, Math.abs(yZero - yTop)); // siempre visible
        ctx.fillRect(xLeft, top, bw, h);
        ctx.restore();

        // Ícono de estado arriba de la barra
        const cx = xLeft + bw / 2;
        const iconY = top - 6;
        this.drawStatusIcon(status, cx, iconY);
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

    // =================== Leyenda (dos líneas) ===================

    drawLegend(x, y) {
        const { ctx } = this;
        ctx.save();
        ctx.font = '10px Arial';
        ctx.textAlign = 'left';

        // Línea 1: OD / OI
        let off = 0;
        ctx.fillStyle = this.config.colors.odFill;
        ctx.fillRect(x + off, y - 6, 12, 12);
        ctx.fillStyle = this.config.colors.text;
        ctx.fillText('OD (SNR)', x + off + 18, y + 4);
        off += 100;

        ctx.fillStyle = this.config.colors.oiFill;
        ctx.fillRect(x + off, y - 6, 12, 12);
        ctx.fillStyle = this.config.colors.text;
        ctx.fillText('OI (SNR)', x + off + 18, y + 4);

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
window.TEOAEScreenerChartView = TEOAEScreenerChartView;
