/**
 * LogoaudiometryModule - Módulo de Logoaudiometría
 * SDT, SRT y UMD con curvas logoaudiométricas
 */

class LogoaudiometryModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'logoaudiometry';
        this.chartView = null;
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
        <div class="form-section">
        <h3 class="section-title">🗣️ Logoaudiometría</h3>
        <p class="section-description">
        Evaluación de la capacidad de detección, recepción e inteligibilidad del habla
        </p>

        <!-- Layout Principal: Formularios (40%) + Preview (60%) -->
        <div style="display: flex; gap: 30px;">
        <!-- Panel de Formularios -->
        <div style="flex: 2; min-width: 400px;">
        <table class="logoaudio-table">
        <thead>
        <tr>
        <th>Prueba</th>
        <th style="color: #dc3545;">OD</th>
        <th style="color: #007bff;">OI</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td class="test-label">SDT (0%)</td>
        <td>
        <input type="number"
        id="sdt_od"
        class="logoaudio-input"
        min="0" max="100" step="5"
        value="${existingData.sdt_deteccion?.oido_derecho || ''}"
        placeholder="dB HL"
        tabindex="1">
        </td>
        <td>
        <input type="number"
        id="sdt_oi"
        class="logoaudio-input"
        min="0" max="100" step="5"
        value="${existingData.sdt_deteccion?.oido_izquierdo || ''}"
        placeholder="dB HL"
        tabindex="9">
        </td>
        </tr>
        <tr>
        <td class="test-label">SRT (50%)</td>
        <td>
        <input type="number"
        id="srt_od"
        class="logoaudio-input"
        min="0" max="100" step="5"
        value="${existingData.srt_audibilidad?.oido_derecho || ''}"
        placeholder="dB HL"
        tabindex="2">
        </td>
        <td>
        <input type="number"
        id="srt_oi"
        class="logoaudio-input"
        min="0" max="100" step="5"
        value="${existingData.srt_audibilidad?.oido_izquierdo || ''}"
        placeholder="dB HL"
        tabindex="10">
        </td>
        </tr>
        ${this.renderUMDRows(existingData.umd_inteligibilidad)}
        </tbody>
        </table>

        <!-- Observaciones -->
        <div class="form-group" style="margin-top: 20px;">
        <label class="label-optional">Observaciones</label>
        <textarea id="logoaudiometry_observations"
        rows="3"
        tabindex="17"
        placeholder="Comentarios adicionales sobre las pruebas de logoaudiometría...">${existingData.observaciones || ''}</textarea>
        </div>
        </div>

        <!-- Panel de Preview -->
        <div style="flex: 3; min-width: 500px;">
        <h4 class="section-subtitle">📊 Curvas Logoaudiométricas</h4>
        <div id="logoaudioPreview" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: white;">
        <canvas id="logoaudioCanvas" width="600" height="400" style="width: 100%; height: auto;"></canvas>
        </div>
        <div style="margin-top: 10px; font-size: 12px; color: #666;">
        <span style="color: #dc3545;">● OD (Rojo)</span> &nbsp;&nbsp;
        <span style="color: #007bff;">● OI (Azul)</span>
        </div>
        </div>
        </div>
        </div>

        <style>
        .logoaudio-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            font-size: 14px;
        }

        .logoaudio-table th {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 8px 12px;
            text-align: center;
            font-weight: 600;
        }

        .logoaudio-table td {
            border: 1px solid #dee2e6;
            padding: 8px;
            text-align: center;
        }

        .test-label {
            background: #f8f9fa;
            font-weight: 500;
            text-align: left !important;
            padding-left: 15px !important;
        }

        .logoaudio-input {
            width: 60px;
            padding: 4px 6px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            text-align: center;
            font-size: 13px;
        }

        .logoaudio-input:focus {
            border-color: #2a5298;
            outline: none;
            box-shadow: 0 0 0 2px rgba(42, 82, 152, 0.1);
        }

        .umd-cell {
            display: flex;
            flex-direction: column;
            gap: 4px;
            align-items: center;
        }

        .umd-inputs {
            display: flex;
            gap: 5px;
            align-items: center;
        }

        .umd-separator {
            font-size: 11px;
            color: #666;
        }
        </style>
        `;
    }

    /**
     * Renderizar filas UMD en formato tabla
     */
    renderUMDRows(umdData) {
        let html = '';

        for (let i = 1; i <= 3; i++) {
            const odIntensidad = umdData?.oido_derecho?.[`umd${i}`]?.intensidad || '';
            const odPorcentaje = umdData?.oido_derecho?.[`umd${i}`]?.porcentaje || '';
            const oiIntensidad = umdData?.oido_izquierdo?.[`umd${i}`]?.intensidad || '';
            const oiPorcentaje = umdData?.oido_izquierdo?.[`umd${i}`]?.porcentaje || '';

            html += `
            <tr>
            <td class="test-label">UMD${i}</td>
            <td>
            <div class="umd-cell">
            <div class="umd-inputs">
            <input type="number"
            id="umd${i}_intensidad_od"
            class="logoaudio-input"
            min="0" max="100" step="5"
            value="${odIntensidad}"
            placeholder="dB"
            tabindex="${1 + i * 2}">
            <span class="umd-separator">/</span>
            <input type="number"
            id="umd${i}_porcentaje_od"
            class="logoaudio-input"
            min="0" max="100" step="1"
            value="${odPorcentaje}"
            placeholder="%"
            tabindex="${2 + i * 2}">
            </div>
            </div>
            </td>
            <td>
            <div class="umd-cell">
            <div class="umd-inputs">
            <input type="number"
            id="umd${i}_intensidad_oi"
            class="logoaudio-input"
            min="0" max="100" step="5"
            value="${oiIntensidad}"
            placeholder="dB"
            tabindex="${9 + i * 2}">
            <span class="umd-separator">/</span>
            <input type="number"
            id="umd${i}_porcentaje_oi"
            class="logoaudio-input"
            min="0" max="100" step="1"
            value="${oiPorcentaje}"
            placeholder="%"
            tabindex="${10 + i * 2}">
            </div>
            </div>
            </td>
            </tr>
            `;
        }

        return html;
    }

    /**
     * Inicializar eventos después de renderizar
     */
    async initEvents() {
        // Cargar vista del gráfico
        await this.loadChartView();

        // Auto-save y update preview al cambiar valores
        const inputs = document.querySelectorAll('#tabsContent input, #tabsContent textarea');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.updateLogoaudioPreview();
                this.app.updateModuleData(this.moduleId, this.getData());
            });
        });

        // Validación en tiempo real
        const numberInputs = document.querySelectorAll('#tabsContent input[type="number"]');
        numberInputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
        });

        // Renderizar preview inicial
        setTimeout(() => {
            this.updateLogoaudioPreview();
        }, 100);
    }

    /**
     * Cargar componente de vista del gráfico
     */
    async loadChartView() {
        try {
            await this.app.loadScript('js/components/views/logoaudio-charts.js');
            this.chartView = new LogoaudioChartView('logoaudioCanvas');
        } catch (error) {
            console.warn('No se pudo cargar logoaudio-chart.js, usando fallback');
            this.chartView = null;
        }
    }

    /**
     * Validar campo individual
     */
    validateField(input) {
        const value = parseFloat(input.value);
        const min = parseFloat(input.min);
        const max = parseFloat(input.max);

        if (input.value && (isNaN(value) || value < min || value > max)) {
            input.classList.add('field-error');
            this.app.notify(`Valor fuera del rango permitido (${min}-${max})`, 'warning');
        } else {
            input.classList.remove('field-error');
        }
    }

    /**
     * Actualizar preview de curvas logoaudiométricas
     */
    updateLogoaudioPreview() {
        if (this.chartView) {
            // Usar componente de vista especializado
            const data = this.getData();
            this.chartView.render(data);
        } else {
            // Fallback simple si no se cargó el componente
            this.renderSimpleFallback();
        }
    }

    /**
     * Fallback simple si no hay componente de vista
     */
    renderSimpleFallback() {
        const canvas = document.getElementById('logoaudioCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = '#666';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Vista previa no disponible', canvas.width/2, canvas.height/2);
        ctx.fillText('(logoaudio-chart.js no cargado)', canvas.width/2, canvas.height/2 + 20);
    }

    /**
     * Obtener datos del formulario
     */
    getData() {
        const getValue = (id) => {
            const element = document.getElementById(id);
            return element ? element.value : '';
        };

        const getNumberValue = (id) => {
            const value = getValue(id);
            return value ? parseFloat(value) : null;
        };

        const data = {
            sdt_deteccion: {
                oido_derecho: getNumberValue('sdt_od'),
                oido_izquierdo: getNumberValue('sdt_oi')
            },
            srt_audibilidad: {
                oido_derecho: getNumberValue('srt_od'),
                oido_izquierdo: getNumberValue('srt_oi')
            },
            umd_inteligibilidad: {
                oido_derecho: {},
                oido_izquierdo: {}
            },
            observaciones: getValue('logoaudiometry_observations')
        };

        // Recopilar UMD 1, 2, 3
        for (let i = 1; i <= 3; i++) {
            const odIntensidad = getNumberValue(`umd${i}_intensidad_od`);
            const odPorcentaje = getNumberValue(`umd${i}_porcentaje_od`);
            const oiIntensidad = getNumberValue(`umd${i}_intensidad_oi`);
            const oiPorcentaje = getNumberValue(`umd${i}_porcentaje_oi`);

            if (odIntensidad !== null || odPorcentaje !== null) {
                data.umd_inteligibilidad.oido_derecho[`umd${i}`] = {
                    intensidad: odIntensidad,
                    porcentaje: odPorcentaje
                };
            }

            if (oiIntensidad !== null || oiPorcentaje !== null) {
                data.umd_inteligibilidad.oido_izquierdo[`umd${i}`] = {
                    intensidad: oiIntensidad,
                    porcentaje: oiPorcentaje
                };
            }
        }

        return data;
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        const errors = [];

        // Validar rangos SDT y SRT
        ['sdt_deteccion', 'srt_audibilidad'].forEach(test => {
            ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
                const value = data[test]?.[ear];
                if (value !== null && (value < 0 || value > 100)) {
                    errors.push(`${test} ${ear} debe estar entre 0-100 dB HL`);
                }
            });
        });

        // Validar UMD
        ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
            for (let i = 1; i <= 3; i++) {
                const umd = data.umd_inteligibilidad?.[ear]?.[`umd${i}`];
                if (umd) {
                    if (umd.intensidad !== null && (umd.intensidad < 0 || umd.intensidad > 100)) {
                        errors.push(`UMD${i} intensidad ${ear} debe estar entre 0-100 dB HL`);
                    }
                    if (umd.porcentaje !== null && (umd.porcentaje < 0 || umd.porcentaje > 100)) {
                        errors.push(`UMD${i} porcentaje ${ear} debe estar entre 0-100%`);
                    }
                }
            }
        });

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    /**
     * Verificar si está completo
     */
    isComplete(data) {
        if (!data) return false;

        // Al menos SDT o SRT debe tener datos en al menos un oído
        const hasSdt = data.sdt_deteccion?.oido_derecho !== null || data.sdt_deteccion?.oido_izquierdo !== null;
        const hasSrt = data.srt_audibilidad?.oido_derecho !== null || data.srt_audibilidad?.oido_izquierdo !== null;

        // O al menos un UMD completo (intensidad Y porcentaje)
        let hasUmd = false;
        ['oido_derecho', 'oido_izquierdo'].forEach(ear => {
            for (let i = 1; i <= 3; i++) {
                const umd = data.umd_inteligibilidad?.[ear]?.[`umd${i}`];
                if (umd?.intensidad !== null && umd?.porcentaje !== null) {
                    hasUmd = true;
                }
            }
        });

        return hasSdt || hasSrt || hasUmd;
    }
}

// Exponer globalmente
window.LogoaudiometryModule = LogoaudiometryModule;
