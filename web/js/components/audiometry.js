/**
 * AudiometryModule - Módulo de Audiometría Tonal
 * ✅ HTML desde templates/es/audiometry.html
 * ✅ CSS desde css/modules/audiometry.css
 * ✅ Gráficos interactivos con modules separados
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
     * Renderizar contenido del módulo usando template
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
            min="-10" max="130" step="5"
            value="${valueOD}"
            placeholder="35">
            </td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="aereo_oi_${freq}"
            data-freq="${freq}"
            data-type="aereo_oi"
            min="-10" max="130" step="5"
            value="${valueOI}"
            placeholder="35">
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
            min="-10" max="80" step="5"
            value="${valueOD}"
            placeholder="20">
            </td>
            <td>
            <input type="number"
            class="audiometry-input"
            id="oseo_oi_${freq}"
            data-freq="${freq}"
            data-type="oseo_oi"
            min="-10" max="80" step="5"
            value="${valueOI}"
            placeholder="20">
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

        // Cargar view externo del gráfico con TODOS los módulos
        await this.loadChartView();

        // Primer render del preview
        setTimeout(() => this.updateAudiogramPreview(), 100);
    }

    /**
     * Cargar view externo del gráfico CON TODOS LOS MÓDULOS
     */
    async loadChartView() {
        try {
            // ✅ CARGAR TODOS LOS SCRIPTS EN ORDEN
            const scripts = [
                'js/components/views/audiogram-charts.js',
                'js/components/views/audiogram/chart-core.js',
                'js/components/views/audiogram/chart-drawing.js',
                'js/components/views/audiogram/chart-symbols.js',
                'js/components/views/audiogram/chart-interaction.js',
                'js/components/views/audiogram/chart-masking.js'
            ];

            for (const script of scripts) {
                await this.app.loadScript(script);
            }

            // ✅ CREAR INSTANCIA DESPUÉS DE CARGAR TODO
            if (window.AudiogramChartView) {
                this.chartView = new window.AudiogramChartView('audiogramCanvas');

                // ✅ ACTIVAR MODO INTERACTIVO
                this.chartView.enableInteractiveMode((freq, toolType, db, state) => {
                    this.handleInteractiveDataChange(freq, toolType, db, state);
                });

                console.log('✅ AudiogramChartView loaded with interactive mode');
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
     * ✅ NUEVA: Manejar cambios de datos desde el modo interactivo
     */
    handleInteractiveDataChange(freq, toolType, db, state) {
        console.log(`🎯 Interactive change: ${freq}Hz, ${toolType}, ${db}dB, state: ${state}`);

        // Determinar el ID del input según el toolType
        let inputId;

        switch (toolType) {
            case 'aereo_od':
                inputId = `aereo_od_${freq}`;
                break;
            case 'aereo_oi':
                inputId = `aereo_oi_${freq}`;
                break;
            case 'oseo_od':
                inputId = `oseo_od_${freq}`;
                break;
            case 'oseo_oi':
                inputId = `oseo_oi_${freq}`;
                break;
            case 'ldl_od':
                inputId = `ldl_od_${freq}`;
                break;
            case 'ldl_oi':
                inputId = `ldl_oi_${freq}`;
                break;
            default:
                console.warn('Unknown toolType:', toolType);
                return;
        }

        // Obtener el input element
        const input = document.getElementById(inputId);
        if (!input) {
            console.warn('Input not found:', inputId);
            return;
        }

        // Actualizar el valor del input según el estado
        if (state === 'empty') {
            input.value = '';
        } else {
            input.value = db.toString();
        }

        // Validar el input y actualizar datos
        this.validateInput(input);
        this.app.updateModuleData(this.moduleId, this.getData());

        // Re-renderizar para mostrar cambios
        this.updateAudiogramPreview();
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

        if (isNaN(value) || value < -10 || value > 130 || value % 5 !== 0) {
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
        if (observaciones && observaciones.value.trim()) {
            data.observaciones = observaciones.value.trim();
        }

        return data;
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        const errors = [];

        if (!data || Object.keys(data).length === 0) {
            errors.push('No se han ingresado datos de audiometría');
            return { isValid: false, errors };
        }

        // Validar que al menos haya algunos umbrales aéreos
        const aereosOD = data.umbrales_aereos?.oido_derecho || {};
        const aereosOI = data.umbrales_aereos?.oido_izquierdo || {};

        if (Object.keys(aereosOD).length === 0 && Object.keys(aereosOI).length === 0) {
            errors.push('Debe ingresar al menos algunos umbrales aéreos');
        }

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

        const aereosOD = data.umbrales_aereos?.oido_derecho || {};
        const aereosOI = data.umbrales_aereos?.oido_izquierdo || {};

        return Object.keys(aereosOD).length > 0 || Object.keys(aereosOI).length > 0;
    }
}

// Registrar el módulo
window.AudiometryModule = AudiometryModule;
