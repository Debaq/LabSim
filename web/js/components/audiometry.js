/**
 * AudiometryModule - Solo Lógica de Negocio
 * ✅ Sin labels hardcodeados - Todo viene del template
 * ✅ HTML en templates/audiometry.html
 * ✅ CSS en css/modules/audiometry.css
 * ✅ Gráficos en js/components/views/audiogram-charts.js
 */
class AudiometryModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'audiometry';
        this.showHighFreq = false;
        this.chartView = null;

        this.frequencies = {
            standard: ['125', '250', '500', '1000', '2000', '4000', '8000'],
            high: ['9000', '10000', '11200', '12500', '14000', '16000', '18000', '20000'],
            bone: ['250', '500', '1000', '2000', '4000'],
            ldl: ['250', '500', '1000', '2000', '4000']
        };
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        await this.loadModuleCSS();
        const lang = this.app.getCurrentLanguage ? this.app.getCurrentLanguage() : 'es';
        const html = await fetch(`templates/${lang}/audiometry.html`).then(r => r.text());

        return this.populateTemplate(html, {
            showHighFreqChecked: this.showHighFreq ? 'checked' : '',
            aereosRows: this.generateAereosRows(existingData.umbrales_aereos),
                                     oseosRows: this.generateOseosRows(existingData.umbrales_oseos),
                                     ldlRows: this.generateLDLRows(existingData.ldl_disconfort),
                                     observaciones: existingData.observaciones || ''
        });
    }

    /**
     * Cargar CSS específico del módulo
     */
    async loadModuleCSS() {
        const cssFile = 'css/modules/audiometry.css';
        if (!document.querySelector(`link[href="${cssFile}"]`)) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = cssFile;
            document.head.appendChild(link);
        }
    }

    /**
     * Poblar template con variables
     */
    populateTemplate(html, data) {
        return html.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return data[key] || '';
        });
    }

    /**
     * Generar filas de vía aérea
     */
    generateAereosRows(existingData) {
        const frequencies = this.showHighFreq
        ? [...this.frequencies.standard, ...this.frequencies.high]
        : this.frequencies.standard;

        return frequencies.map((freq, index) => {
            const valueOD = existingData?.oido_derecho?.[freq] || '';
            const valueOI = existingData?.oido_izquierdo?.[freq] || '';
            const isHighFreq = this.frequencies.high.includes(freq);
            const displayStyle = isHighFreq && !this.showHighFreq ? 'display: none;' : '';

            return `
            <tr class="${isHighFreq ? 'high-freq-row' : ''}" style="${displayStyle}">
            <td class="freq-label">${freq} Hz</td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="aereo_od_${freq}"
            data-freq="${freq}"
            data-type="aereo_od"
            min="0" max="130" step="5"
            value="${valueOD}"
            placeholder="-">
            </td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="aereo_oi_${freq}"
            data-freq="${freq}"
            data-type="aereo_oi"
            min="0" max="130" step="5"
            value="${valueOI}"
            placeholder="-">
            </td>
            </tr>`;
        }).join('');
    }

    /**
     * Generar filas de vía ósea
     */
    generateOseosRows(existingData) {
        return this.frequencies.bone.map(freq => {
            const valueOD = existingData?.oido_derecho?.[freq] || '';
            const valueOI = existingData?.oido_izquierdo?.[freq] || '';

            return `
            <tr>
            <td class="freq-label">${freq} Hz</td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="oseo_od_${freq}"
            data-freq="${freq}"
            data-type="oseo_od"
            min="0" max="130" step="5"
            value="${valueOD}"
            placeholder="-">
            </td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="oseo_oi_${freq}"
            data-freq="${freq}"
            data-type="oseo_oi"
            min="0" max="130" step="5"
            value="${valueOI}"
            placeholder="-">
            </td>
            </tr>`;
        }).join('');
    }

    /**
     * Generar filas de LDL
     */
    generateLDLRows(existingData) {
        return this.frequencies.ldl.map(freq => {
            const valueOD = existingData?.oido_derecho?.[freq] || '';
            const valueOI = existingData?.oido_izquierdo?.[freq] || '';

            return `
            <tr>
            <td class="freq-label">${freq} Hz</td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="ldl_od_${freq}"
            data-freq="${freq}"
            data-type="ldl_od"
            min="60" max="130" step="5"
            value="${valueOD}"
            placeholder="120">
            </td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="ldl_oi_${freq}"
            data-freq="${freq}"
            data-type="ldl_oi"
            min="60" max="130" step="5"
            value="${valueOI}"
            placeholder="120">
            </td>
            </tr>`;
        }).join('');
    }

    /**
     * Inicializar eventos
     */
    async initEvents() {
        // Toggle de altas frecuencias
        const showHighFreqCheck = document.getElementById('showHighFreq');
        if (showHighFreqCheck) {
            showHighFreqCheck.addEventListener('change', (e) => {
                this.showHighFreq = e.target.checked;
                this.toggleHighFrequencies();
            });
        }

        // Inputs de audiometría
        const inputs = document.querySelectorAll('.audiometry-input');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.validateInput(input);
                this.updateAudiogramPreview();
                this.app.updateModuleData(this.moduleId, this.getData());
            });
        });

        // Observaciones
        const observaciones = document.getElementById('observaciones');
        if (observaciones) {
            observaciones.addEventListener('input', () => {
                this.app.updateModuleData(this.moduleId, this.getData());
            });
        }

        // Cargar view externo del gráfico
        await this.loadChartView();

        // Primer render del preview
        setTimeout(() => this.updateAudiogramPreview(), 100);
    }

    /**
     * Cargar view externo del gráfico
     */
    async loadChartView() {
        try {
            await this.app.loadScript('js/components/views/audiogram-charts.js');
            if (window.AudiogramChartView) {
                this.chartView = new window.AudiogramChartView('audiogramCanvas');
                console.log('✅ AudiogramChartView loaded successfully');
            } else {
                this.chartView = null;
                console.warn('⚠️ AudiogramChartView class not found');
            }
        } catch (e) {
            console.warn('📋 Could not load audiogram-charts.js:', e.message);
            this.chartView = null;
        }
    }

    /**
     * Toggle altas frecuencias
     */
    toggleHighFrequencies() {
        const highFreqRows = document.querySelectorAll('.high-freq-row');
        highFreqRows.forEach(row => {
            row.style.display = this.showHighFreq ? 'table-row' : 'none';
        });
        this.updateAudiogramPreview();
    }

    /**
     * Validar input
     */
    validateInput(input) {
        const value = parseInt(input.value);
        input.classList.remove('field-error', 'field-success');

        if (input.value === '') return true;

        if (isNaN(value) || value < 0 || value > 130 || value % 5 !== 0) {
            input.classList.add('field-error');
            return false;
        }

        input.classList.add('field-success');
        return true;
    }

    /**
     * Actualizar preview - Solo delegación al view externo
     */
    updateAudiogramPreview() {
        if (!this.chartView) return;

        const data = this.getData();
        const freqsToShow = this.showHighFreq
        ? [...this.frequencies.standard, ...this.frequencies.high]
        : this.frequencies.standard;

        try {
            this.chartView.render(data, {
                showHighFreq: this.showHighFreq,
                freqs: freqsToShow
            });
        } catch (error) {
            console.warn('Error rendering audiogram:', error);
        }
    }

    /**
     * Obtener datos del formulario
     */
    getData() {
        const data = {
            umbrales_aereos: { oido_derecho: {}, oido_izquierdo: {} },
            umbrales_oseos: { oido_derecho: {}, oido_izquierdo: {} },
            ldl_disconfort: { oido_derecho: {}, oido_izquierdo: {} }
        };

        // Recopilar umbrales aéreos y óseos
        ['aereo', 'oseo'].forEach(type => {
            const frequencies = type === 'aereo'
            ? (this.showHighFreq ? [...this.frequencies.standard, ...this.frequencies.high] : this.frequencies.standard)
            : this.frequencies.bone;

            frequencies.forEach(freq => {
                ['od', 'oi'].forEach(ear => {
                    const input = document.getElementById(`${type}_${ear}_${freq}`);
                    if (input && input.value !== '') {
                        const earKey = ear === 'od' ? 'oido_derecho' : 'oido_izquierdo';
                        const typeKey = type === 'aereo' ? 'umbrales_aereos' : 'umbrales_oseos';
                        data[typeKey][earKey][freq] = parseInt(input.value);
                    }
                });
            });
        });

        // Recopilar LDL
        this.frequencies.ldl.forEach(freq => {
            ['od', 'oi'].forEach(ear => {
                const input = document.getElementById(`ldl_${ear}_${freq}`);
                if (input && input.value !== '') {
                    const earKey = ear === 'od' ? 'oido_derecho' : 'oido_izquierdo';
                    data.ldl_disconfort[earKey][freq] = parseInt(input.value);
                }
            });
        });

        // Observaciones
        const observaciones = document.getElementById('observaciones');
        if (observaciones) {
            data.observaciones = observaciones.value;
        }

        return data;
    }

    /**
     * Validar datos
     */
    validate(data) {
        const errors = [];

        if (!data || typeof data !== 'object') {
            errors.push('Invalid audiometry data');
            return { isValid: false, errors };
        }

        const hasAereoOD = data.umbrales_aereos?.oido_derecho &&
        Object.keys(data.umbrales_aereos.oido_derecho).length > 0;
        const hasAereoOI = data.umbrales_aereos?.oido_izquierdo &&
        Object.keys(data.umbrales_aereos.oido_izquierdo).length > 0;

        if (!hasAereoOD && !hasAereoOI) {
            errors.push('Must enter at least some air conduction thresholds');
        }

        return { isValid: errors.length === 0, errors };
    }

    /**
     * Verificar si está completo
     */
    isComplete(data) {
        if (!data) return false;

        const hasAereoOD = data.umbrales_aereos?.oido_derecho &&
        Object.keys(data.umbrales_aereos.oido_derecho).length >= 3;
        const hasAereoOI = data.umbrales_aereos?.oido_izquierdo &&
        Object.keys(data.umbrales_aereos.oido_izquierdo).length >= 3;

        return hasAereoOD || hasAereoOI;
    }
}

window.AudiometryModule = AudiometryModule;
