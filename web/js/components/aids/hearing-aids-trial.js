/**
 * HearingAidsTrialSection - Sección de Prueba de Audífonos
 * Documentación fotográfica, pruebas electroacústicas, mediciones en oído real y evaluación de uso
 */

class HearingAidsTrialSection {
    constructor(app, parentModule) {
        this.app = app;
        this.parent = parentModule;
        this.sectionId = 'trial';

        // Almacenamiento temporal de imágenes
        this.uploadedImages = {
            audifono_estado: [],
            molde_estado: [],
            accesorios: []
        };

        // Frecuencias para mediciones
        this.frequencies = ['250', '500', '1000', '2000', '4000', '8000'];

        // Vistas de gráficos (se cargarán dinámicamente)
        this.chartViews = {
            electroacoustic: null,
            realEar: null,
            compression: null
        };
    }

    /**
     * Renderizar contenido de la sección
     */
    async render(existingData = {}) {
        // Cargar imágenes existentes si las hay
        if (existingData.imagenes) {
            this.uploadedImages = { ...existingData.imagenes };
        }

        return `
        <div class="aids-trial-content">

        <!-- Documentación Fotográfica (Compacta) -->
        <div class="form-group">
        <h4 class="section-subtitle">📸 Documentación Visual</h4>
        <div class="photo-compact-grid">
        <div class="photo-compact-item">
        <label>🎧 Audífono</label>
        <div class="compact-upload" onclick="document.getElementById('audifono_input').click()">
        <span>+</span>
        <input type="file" id="audifono_input" accept="image/*" multiple style="display: none;">
        </div>
        <div class="compact-thumbs" id="audifono_thumbs">
        ${this.renderCompactThumbs('audifono_estado')}
        </div>
        </div>
        <div class="photo-compact-item">
        <label>🔌 Molde/Domo</label>
        <div class="compact-upload" onclick="document.getElementById('molde_input').click()">
        <span>+</span>
        <input type="file" id="molde_input" accept="image/*" multiple style="display: none;">
        </div>
        <div class="compact-thumbs" id="molde_thumbs">
        ${this.renderCompactThumbs('molde_estado')}
        </div>
        </div>
        <div class="photo-compact-item">
        <label>🔋 Accesorios</label>
        <div class="compact-upload" onclick="document.getElementById('accesorios_input').click()">
        <span>+</span>
        <input type="file" id="accesorios_input" accept="image/*" multiple style="display: none;">
        </div>
        <div class="compact-thumbs" id="accesorios_thumbs">
        ${this.renderCompactThumbs('accesorios')}
        </div>
        </div>
        </div>
        </div>

        <!-- Evaluación de Uso (Texto Libre) -->
        <div class="form-group">
        <h4 class="section-subtitle">👤 Evaluación de Uso del Paciente</h4>
        <div class="form-row">
        <div class="form-col-2">
        <label class="label-optional">Rutina y Problemas de Uso</label>
        <textarea id="rutina_problemas"
        rows="3"
        tabindex="1"
        placeholder="Cómo usa sus audífonos, cuándo los usa, problemas específicos que reporta...">${existingData.evaluacion_uso?.rutina_problemas || ''}</textarea>
        </div>
        <div class="form-col-2">
        <label class="label-optional">Situaciones Problemáticas y Mantenimiento</label>
        <textarea id="situaciones_mantenimiento"
        rows="3"
        tabindex="2"
        placeholder="Ambientes donde fallan, hábitos de limpieza y cuidado...">${existingData.evaluacion_uso?.situaciones_mantenimiento || ''}</textarea>
        </div>
        </div>
        </div>

        <!-- Pruebas Electroacústicas en Caja -->
        <div class="form-group">
        <h4 class="section-subtitle">🔧 Pruebas Electroacústicas en Caja de Prueba</h4>

        <div style="display: flex; gap: 30px;">
        <!-- Panel de Datos -->
        <div style="flex: 1;">
        <!-- Mediciones Básicas -->
        <div class="electroacoustic-section">
        <h5 class="measurement-title">Mediciones Básicas</h5>
        <div class="form-row">
        <div class="form-col-3">
        <label>OSPL90 (dB SPL)</label>
        <input type="number"
        id="ospl90"
        min="90" max="140" step="1"
        value="${existingData.electroacusticas?.ospl90 || ''}"
        placeholder="115"
        tabindex="3">
        </div>
        <div class="form-col-3">
        <label>Ganancia HFA (dB)</label>
        <input type="number"
        id="ganancia_hfa"
        min="0" max="80" step="1"
        value="${existingData.electroacusticas?.ganancia_hfa || ''}"
        placeholder="35"
        tabindex="4">
        </div>
        <div class="form-col-3">
        <label>THD 500Hz (%)</label>
        <input type="number"
        id="thd_500"
        min="0" max="10" step="0.1"
        value="${existingData.electroacusticas?.thd_500 || ''}"
        placeholder="2.5"
        tabindex="5">
        </div>
        </div>

        <div class="form-row">
        <div class="form-col-3">
        <label>THD 800Hz (%)</label>
        <input type="number"
        id="thd_800"
        min="0" max="10" step="0.1"
        value="${existingData.electroacusticas?.thd_800 || ''}"
        placeholder="3.2"
        tabindex="6">
        </div>
        <div class="form-col-3">
        <label>Ruido EIN (dB SPL)</label>
        <input type="number"
        id="ruido_ein"
        min="15" max="35" step="1"
        value="${existingData.electroacusticas?.ruido_ein || ''}"
        placeholder="23"
        tabindex="7">
        </div>
        <div class="form-col-3">
        <label>Corriente (mA)</label>
        <input type="number"
        id="corriente_bateria"
        min="0.5" max="5" step="0.1"
        value="${existingData.electroacusticas?.corriente_bateria || ''}"
        placeholder="1.2"
        tabindex="8">
        </div>
        </div>
        </div>

        <!-- Respuesta en Frecuencia -->
        <div class="electroacoustic-section">
        <h5 class="measurement-title">Respuesta en Frecuencia (Ganancia por frecuencia)</h5>
        <div class="ear-selector">
        <div class="ear-column">
        <div class="ear-title" style="color: #dc3545;">🔴 Oído Derecho</div>
        <div class="frequency-grid">
        ${this.renderFrequencyGrid('freq_response', 'od', existingData.electroacusticas?.respuesta_frecuencia?.oido_derecho, 9)}
        </div>
        </div>
        <div class="ear-column">
        <div class="ear-title" style="color: #007bff;">🔵 Oído Izquierdo</div>
        <div class="frequency-grid">
        ${this.renderFrequencyGrid('freq_response', 'oi', existingData.electroacusticas?.respuesta_frecuencia?.oido_izquierdo, 15)}
        </div>
        </div>
        </div>
        </div>

        <!-- Características de Compresión -->
        <div class="electroacoustic-section">
        <h5 class="measurement-title">Características de Compresión</h5>
        <div class="form-row">
        <div class="form-col-4">
        <label>Ratio de Compresión</label>
        <select id="compression_ratio" tabindex="21">
        <option value="">Seleccionar...</option>
        <option value="1.5:1" ${this.getSelected(existingData.electroacusticas?.compression_ratio, '1.5:1')}>1.5:1</option>
        <option value="2:1" ${this.getSelected(existingData.electroacusticas?.compression_ratio, '2:1')}>2:1</option>
        <option value="3:1" ${this.getSelected(existingData.electroacusticas?.compression_ratio, '3:1')}>3:1</option>
        <option value="4:1" ${this.getSelected(existingData.electroacusticas?.compression_ratio, '4:1')}>4:1</option>
        <option value="6:1" ${this.getSelected(existingData.electroacusticas?.compression_ratio, '6:1')}>6:1</option>
        <option value="10:1" ${this.getSelected(existingData.electroacusticas?.compression_ratio, '10:1')}>10:1</option>
        </select>
        </div>
        <div class="form-col-4">
        <label>Knee Point (dB SPL)</label>
        <input type="number"
        id="knee_point"
        min="40" max="80" step="5"
        value="${existingData.electroacusticas?.knee_point || ''}"
        placeholder="55"
        tabindex="22">
        </div>
        <div class="form-col-4">
        <label>Tiempo Ataque (ms)</label>
        <input type="number"
        id="attack_time"
        min="1" max="50" step="1"
        value="${existingData.electroacusticas?.attack_time || ''}"
        placeholder="5"
        tabindex="23">
        </div>
        <div class="form-col-4">
        <label>Tiempo Release (ms)</label>
        <input type="number"
        id="release_time"
        min="10" max="1000" step="10"
        value="${existingData.electroacusticas?.release_time || ''}"
        placeholder="150"
        tabindex="24">
        </div>
        </div>
        </div>
        </div>

        <!-- Panel de Gráficos -->
        <div style="flex: 1; min-width: 400px;">
        <h5 class="measurement-title">📊 Curvas Electroacústicas</h5>

        <!-- Respuesta en Frecuencia -->
        <div class="chart-container">
        <h6>Respuesta en Frecuencia</h6>
        <canvas id="freqResponseCanvas" width="400" height="200"></canvas>
        </div>

        <!-- Curvas de Compresión -->
        <div class="chart-container">
        <h6>Curvas de Compresión</h6>
        <canvas id="compressionCanvas" width="400" height="200"></canvas>
        </div>
        </div>
        </div>
        </div>

        <!-- Mediciones en Oído Real (REM) -->
        <div class="form-group">
        <h4 class="section-subtitle">👂 Mediciones en Oído Real (REM)</h4>

        <div style="display: flex; gap: 30px;">
        <!-- Panel de Datos REM -->
        <div style="flex: 1;">

        <!-- REUR y RECD -->
        <div class="rem-section">
        <h5 class="measurement-title">Mediciones de Referencia</h5>
        <div class="form-row">
        <div class="form-col-2">
        <label>REUR Promedio (dB SPL)</label>
        <input type="number"
        id="reur_promedio"
        min="5" max="25" step="1"
        value="${existingData.rem?.reur_promedio || ''}"
        placeholder="12"
        tabindex="25">
        </div>
        <div class="form-col-2">
        <label>RECD Promedio (dB)</label>
        <input type="number"
        id="recd_promedio"
        min="0" max="15" step="1"
        value="${existingData.rem?.recd_promedio || ''}"
        placeholder="8"
        tabindex="26">
        </div>
        </div>
        </div>

        <!-- REIG por Frecuencia -->
        <div class="rem-section">
        <h5 class="measurement-title">REIG - Ganancia de Inserción (dB)</h5>
        <div class="ear-selector">
        <div class="ear-column">
        <div class="ear-title" style="color: #dc3545;">🔴 Oído Derecho</div>
        <div class="frequency-grid">
        ${this.renderFrequencyGrid('reig', 'od', existingData.rem?.reig?.oido_derecho, 27)}
        </div>
        </div>
        <div class="ear-column">
        <div class="ear-title" style="color: #007bff;">🔵 Oído Izquierdo</div>
        <div class="frequency-grid">
        ${this.renderFrequencyGrid('reig', 'oi', existingData.rem?.reig?.oido_izquierdo, 33)}
        </div>
        </div>
        </div>
        </div>

        <!-- Comparación con Targets -->
        <div class="rem-section">
        <h5 class="measurement-title">Comparación con Targets</h5>
        <div class="form-row">
        <div class="form-col-3">
        <label>Fórmula Prescriptiva</label>
        <select id="formula_prescriptiva" tabindex="39">
        <option value="">Seleccionar...</option>
        <option value="nal_nl2" ${this.getSelected(existingData.rem?.formula_prescriptiva, 'nal_nl2')}>NAL-NL2</option>
        <option value="dsl_v5" ${this.getSelected(existingData.rem?.formula_prescriptiva, 'dsl_v5')}>DSL v5</option>
        <option value="nal_nl1" ${this.getSelected(existingData.rem?.formula_prescriptiva, 'nal_nl1')}>NAL-NL1</option>
        <option value="propietaria" ${this.getSelected(existingData.rem?.formula_prescriptiva, 'propietaria')}>Propietaria</option>
        </select>
        </div>
        <div class="form-col-3">
        <label>Match Target Promedio (%)</label>
        <input type="number"
        id="match_target"
        min="60" max="100" step="1"
        value="${existingData.rem?.match_target || ''}"
        placeholder="85"
        tabindex="40">
        </div>
        <div class="form-col-3">
        <label>Desviación RMS (dB)</label>
        <input type="number"
        id="desviacion_rms"
        min="0" max="10" step="0.5"
        value="${existingData.rem?.desviacion_rms || ''}"
        placeholder="3.2"
        tabindex="41">
        </div>
        </div>
        </div>
        </div>

        <!-- Panel de Gráficos REM -->
        <div style="flex: 1; min-width: 400px;">
        <h5 class="measurement-title">📊 Curvas REM</h5>

        <!-- REIG vs Target -->
        <div class="chart-container">
        <h6>REIG vs Target</h6>
        <canvas id="reigTargetCanvas" width="400" height="200"></canvas>
        </div>

        <!-- REAR vs Target -->
        <div class="chart-container">
        <h6>REAR vs Target</h6>
        <canvas id="rearTargetCanvas" width="400" height="200"></canvas>
        </div>
        </div>
        </div>
        </div>

        <!-- Verificación de Algoritmos -->
        <div class="form-group">
        <h4 class="section-subtitle">🧠 Verificación de Algoritmos</h4>

        <div class="form-row">
        <div class="form-col-4">
        <label>Reducción de Ruido</label>
        <select id="reduccion_ruido" tabindex="42">
        <option value="">No probado</option>
        <option value="excelente" ${this.getSelected(existingData.algoritmos?.reduccion_ruido, 'excelente')}>Excelente</option>
        <option value="buena" ${this.getSelected(existingData.algoritmos?.reduccion_ruido, 'buena')}>Buena</option>
        <option value="regular" ${this.getSelected(existingData.algoritmos?.reduccion_ruido, 'regular')}>Regular</option>
        <option value="deficiente" ${this.getSelected(existingData.algoritmos?.reduccion_ruido, 'deficiente')}>Deficiente</option>
        </select>
        </div>
        <div class="form-col-4">
        <label>Direccionalidad</label>
        <select id="direccionalidad" tabindex="43">
        <option value="">No probado</option>
        <option value="excelente" ${this.getSelected(existingData.algoritmos?.direccionalidad, 'excelente')}>Excelente</option>
        <option value="buena" ${this.getSelected(existingData.algoritmos?.direccionalidad, 'buena')}>Buena</option>
        <option value="regular" ${this.getSelected(existingData.algoritmos?.direccionalidad, 'regular')}>Regular</option>
        <option value="deficiente" ${this.getSelected(existingData.algoritmos?.direccionalidad, 'deficiente')}>Deficiente</option>
        </select>
        </div>
        <div class="form-col-4">
        <label>Supresión Feedback</label>
        <select id="supresion_feedback" tabindex="44">
        <option value="">No probado</option>
        <option value="excelente" ${this.getSelected(existingData.algoritmos?.supresion_feedback, 'excelente')}>Excelente</option>
        <option value="buena" ${this.getSelected(existingData.algoritmos?.supresion_feedback, 'buena')}>Buena</option>
        <option value="regular" ${this.getSelected(existingData.algoritmos?.supresion_feedback, 'regular')}>Regular</option>
        <option value="deficiente" ${this.getSelected(existingData.algoritmos?.supresion_feedback, 'deficiente')}>Deficiente</option>
        </select>
        </div>
        </div>

        <div class="form-row">
        <div class="form-col-2">
        <label>Conectividad Bluetooth</label>
        <select id="conectividad_bluetooth" tabindex="45">
        <option value="">No aplica</option>
        <option value="estable" ${this.getSelected(existingData.algoritmos?.conectividad_bluetooth, 'estable')}>Estable</option>
        <option value="intermitente" ${this.getSelected(existingData.algoritmos?.conectividad_bluetooth, 'intermitente')}>Intermitente</option>
        <option value="problematica" ${this.getSelected(existingData.algoritmos?.conectividad_bluetooth, 'problematica')}>Problemática</option>
        </select>
        </div>
        <div class="form-col-2">
        <label class="label-optional">Observaciones Algoritmos</label>
        <textarea id="observaciones_algoritmos"
        rows="2"
        tabindex="46"
        placeholder="Comentarios sobre el funcionamiento de algoritmos específicos...">${existingData.algoritmos?.observaciones || ''}</textarea>
        </div>
        </div>
        </div>

        <!-- Prueba del Paciente y Decisión Final -->
        <div class="form-group">
        <h4 class="section-subtitle">🧪 Prueba del Paciente y Decisión Final</h4>

        <div class="form-row">
        <div class="form-col-auto">
        <label style="display: flex; align-items: center; gap: 10px;">
        <input type="checkbox"
        id="tiene_prueba_paciente"
        ${existingData.tiene_prueba_paciente ? 'checked' : ''}
        tabindex="47">
        <strong>Se realizó prueba con el paciente</strong>
        </label>
        </div>
        </div>

        <!-- Detalles de la Prueba del Paciente -->
        <div id="detalles_prueba_paciente" style="display: none;">

        <div class="trial-section">
        <h5 class="measurement-title">Especificaciones del Audífono Probado</h5>
        <div class="form-row">
        <div class="form-col-4">
        <label>Marca y Modelo</label>
        <input type="text"
        id="prueba_marca_modelo"
        value="${existingData.prueba_paciente?.marca_modelo || ''}"
        placeholder="Phonak Paradise P90-R"
        tabindex="48">
        </div>
        <div class="form-col-4">
        <label>Tiempo de Prueba</label>
        <select id="tiempo_prueba" tabindex="49">
        <option value="">Seleccionar...</option>
        <option value="inmediata" ${this.getSelected(existingData.prueba_paciente?.tiempo_prueba, 'inmediata')}>Prueba inmediata</option>
        <option value="1_semana" ${this.getSelected(existingData.prueba_paciente?.tiempo_prueba, '1_semana')}>1 semana</option>
        <option value="2_semanas" ${this.getSelected(existingData.prueba_paciente?.tiempo_prueba, '2_semanas')}>2 semanas</option>
        <option value="1_mes" ${this.getSelected(existingData.prueba_paciente?.tiempo_prueba, '1_mes')}>1 mes</option>
        </select>
        </div>
        <div class="form-col-4">
        <label>Satisfacción General (1-10)</label>
        <select id="satisfaccion_prueba" tabindex="50">
        <option value="">-</option>
        ${this.renderScaleOptions(existingData.prueba_paciente?.satisfaccion_general)}
        </select>
        </div>
        <div class="form-col-4">
        <label class="label-required">Decisión Final</label>
        <select id="decision_final" tabindex="51">
        <option value="">Seleccionar...</option>
        <option value="acepta" ${this.getSelected(existingData.prueba_paciente?.decision_final, 'acepta')}>Acepta</option>
        <option value="rechaza" ${this.getSelected(existingData.prueba_paciente?.decision_final, 'rechaza')}>Rechaza</option>
        <option value="solicita_ajustes" ${this.getSelected(existingData.prueba_paciente?.decision_final, 'solicita_ajustes')}>Solicita ajustes</option>
        <option value="necesita_mas_tiempo" ${this.getSelected(existingData.prueba_paciente?.decision_final, 'necesita_mas_tiempo')}>Necesita más tiempo</option>
        </select>
        </div>
        </div>

        <div class="form-row">
        <div class="form-col">
        <label class="label-optional">Comentarios de la Prueba</label>
        <textarea id="comentarios_prueba"
        rows="2"
        tabindex="52"
        placeholder="Experiencia del paciente, ajustes realizados, razones de aceptación/rechazo...">${existingData.prueba_paciente?.comentarios || ''}</textarea>
        </div>
        </div>
        </div>
        </div>
        </div>

        <!-- Observaciones Generales -->
        <div class="form-group">
        <label class="label-optional">Observaciones Generales</label>
        <textarea id="observaciones_trial"
        rows="3"
        tabindex="53"
        placeholder="Comentarios adicionales sobre las pruebas electroacústicas, mediciones REM, comportamiento de algoritmos, etc.">${existingData.observaciones || ''}</textarea>
        </div>
        </div>

        <style>
        .aids-trial-content {
            animation: slideIn 0.3s ease-out;
        }

        /* Fotos Compactas */
        .photo-compact-grid {
            display: flex;
            gap: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 3px solid #28a745;
        }

        .photo-compact-item {
            flex: 1;
            text-align: center;
        }

        .photo-compact-item label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #495057;
        }

        .compact-upload {
            width: 60px;
            height: 60px;
            border: 2px dashed #dee2e6;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            background: white;
            margin: 0 auto 8px;
            transition: all 0.3s ease;
            font-size: 24px;
            color: #28a745;
        }

        .compact-upload:hover {
            border-color: #28a745;
            background: rgba(40, 167, 69, 0.05);
        }

        .compact-thumbs {
            display: flex;
            gap: 4px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .compact-thumb {
            width: 30px;
            height: 30px;
            border-radius: 3px;
            overflow: hidden;
            border: 1px solid #dee2e6;
            position: relative;
            cursor: pointer;
        }

        .compact-thumb img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .compact-thumb-remove {
            position: absolute;
            top: -2px;
            right: -2px;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 50%;
            width: 16px;
            height: 16px;
            font-size: 10px;
            cursor: pointer;
            display: none;
        }

        .compact-thumb:hover .compact-thumb-remove {
            display: block;
        }

        /* Secciones de Mediciones */
        .electroacoustic-section, .rem-section, .trial-section {
            margin-bottom: 20px;
            padding: 15px;
            background: #f1f8ff;
            border-radius: 6px;
            border-left: 3px solid #007bff;
        }

        .measurement-title {
            color: #2a5298;
            font-size: 0.95em;
            margin-bottom: 12px;
            font-weight: 600;
        }

        .frequency-grid {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 6px;
            align-items: center;
        }

        .freq-label {
            font-weight: 600;
            padding: 6px;
            background: linear-gradient(135deg, #e9ecef, #f8f9fa);
            border-radius: 3px;
            text-align: center;
            color: #495057;
            font-size: 11px;
            min-width: 40px;
        }

        .freq-input {
            padding: 4px 6px;
            border: 1px solid #dee2e6;
            border-radius: 3px;
            text-align: center;
            font-weight: 500;
            font-size: 12px;
            width: 100%;
        }

        .freq-input:focus {
            border-color: #007bff;
            outline: none;
            box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
        }

        /* Contenedores de Gráficos */
        .chart-container {
            margin-bottom: 15px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 10px;
            background: white;
        }

        .chart-container h6 {
            margin: 0 0 8px 0;
            font-size: 12px;
            color: #495057;
            text-align: center;
            font-weight: 600;
        }

        .chart-container canvas {
            width: 100%;
            height: auto;
            display: block;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-10px); }
            to { opacity: 1; transform: translateX(0); }
        }
        </style>
        `;
    }

    /**
     * Helper para valores seleccionados
     */
    getSelected(currentValue, optionValue) {
        return currentValue === optionValue ? 'selected' : '';
    }

    /**
     * Renderizar thumbnails compactos
     */
    renderCompactThumbs(category) {
        const images = this.uploadedImages[category] || [];
        return images.map((image, index) => `
        <div class="compact-thumb">
        <img src="${image.dataUrl}" alt="Img ${index + 1}">
        <button class="compact-thumb-remove" onclick="window.removeTrialImage('${category}', ${index})" title="Eliminar">×</button>
        </div>
        `).join('');
    }

    /**
     * Renderizar grid de frecuencias
     */
    renderFrequencyGrid(type, ear, data = {}, startTabIndex = 1) {
        return this.frequencies.map((freq, index) => {
            const value = data ? data[freq] || '' : '';
            const tabIndex = startTabIndex + index;

            return `
            <div class="freq-label">${freq}</div>
            <input type="number"
            id="${type}_${ear}_${freq}"
            class="freq-input"
            min="-10" max="80" step="1"
            value="${value}"
            placeholder="dB"
            tabindex="${tabIndex}">
            `;
        }).join('');
    }

    /**
     * Renderizar opciones de escala 1-10
     */
    renderScaleOptions(selectedValue) {
        let options = '';
        for (let i = 1; i <= 10; i++) {
            const selected = selectedValue == i ? 'selected' : '';
            const description = i <= 3 ? 'Malo' : i <= 5 ? 'Regular' : i <= 7 ? 'Bueno' : i <= 9 ? 'Muy bueno' : 'Excelente';
            options += `<option value="${i}" ${selected}>${i} (${description})</option>`;
        }
        return options;
    }

    /**
     * Inicializar eventos después de renderizar
     */
    async initEvents() {
        // Cargar vistas de gráficos
        await this.loadChartViews();

        // Configurar uploads de imágenes
        this.setupImageUploads();

        // Configurar visibilidad condicional
        this.setupConditionalSections();

        // Auto-save y update preview
        this.setupAutoSave();

        // Validación
        this.setupValidation();

        // Renderizar previews iniciales
        setTimeout(() => {
            this.updateElectroacousticPreviews();
            this.updateREMPreviews();
        }, 100);
    }

    /**
     * Cargar componentes de vista de gráficos
     */
    async loadChartViews() {
        const chartFiles = [
            { file: 'electroacoustic-chart.js', view: 'ElectroacousticChartView', canvas: 'freqResponseCanvas', key: 'electroacoustic' },
            { file: 'compression-chart.js', view: 'CompressionChartView', canvas: 'compressionCanvas', key: 'compression' },
            { file: 'rem-chart.js', view: 'REMChartView', canvas: 'reigTargetCanvas', key: 'realEar' }
        ];

        for (const chart of chartFiles) {
            try {
                await this.app.loadScript(`js/components/views/${chart.file}`);
                if (window[chart.view]) {
                    this.chartViews[chart.key] = new window[chart.view](chart.canvas);
                }
            } catch (error) {
                console.warn(`${chart.file} no disponible`);
                this.chartViews[chart.key] = null;
            }
        }
    }

    /**
     * Configurar uploads de imágenes
     */
    setupImageUploads() {
        const categories = ['audifono', 'molde', 'accesorios'];

        categories.forEach(category => {
            const input = document.getElementById(`${category}_input`);

            if (input) {
                input.addEventListener('change', (e) => {
                    this.handleImageUpload(e, category);
                });
            }
        });

        // Exponer método para eliminar imágenes
        window.removeTrialImage = (category, index) => {
            this.removeImage(category, index);
        };
    }

    /**
     * Manejar upload de imágenes
     */
    handleImageUpload(event, category) {
        const files = Array.from(event.target.files);
        this.processImageFiles(files, category);
        event.target.value = '';
    }

    /**
     * Procesar archivos de imagen
     */
    processImageFiles(files, category) {
        const imageFiles = files.filter(file => file.type.startsWith('image/'));

        if (imageFiles.length === 0) {
            this.app.notify('Solo archivos de imagen permitidos', 'warning');
            return;
        }

        const maxImages = 3; // Reducido para versión compacta
        const currentImages = this.uploadedImages[category + '_estado'] || [];

        if (currentImages.length + imageFiles.length > maxImages) {
            this.app.notify(`Máximo ${maxImages} imágenes por categoría`, 'warning');
            return;
        }

        imageFiles.forEach(file => {
            if (file.size > 2 * 1024 * 1024) { // 2MB máximo para versión compacta
                this.app.notify(`Imagen muy grande (máx 2MB)`, 'warning');
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                const imageData = {
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    dataUrl: e.target.result,
                    uploadDate: new Date().toISOString()
                };

                const categoryKey = category + '_estado';
                if (!this.uploadedImages[categoryKey]) {
                    this.uploadedImages[categoryKey] = [];
                }
                this.uploadedImages[categoryKey].push(imageData);

                this.updateImageDisplay(category);
                this.saveData();
            };

            reader.readAsDataURL(file);
        });
    }

    /**
     * Actualizar visualización de imágenes
     */
    updateImageDisplay(category) {
        const container = document.getElementById(`${category}_thumbs`);
        if (container) {
            container.innerHTML = this.renderCompactThumbs(category + '_estado');
        }
    }

    /**
     * Eliminar imagen
     */
    removeImage(category, index) {
        const categoryKey = category;
        if (this.uploadedImages[categoryKey] && this.uploadedImages[categoryKey][index]) {
            this.uploadedImages[categoryKey].splice(index, 1);

            const actualCategory = categoryKey.replace('_estado', '');
            this.updateImageDisplay(actualCategory);
            this.saveData();
        }
    }

    /**
     * Configurar secciones condicionales
     */
    setupConditionalSections() {
        const tienePruebaCheckbox = document.getElementById('tiene_prueba_paciente');
        if (!tienePruebaCheckbox) return;

        const detallesPrueba = document.getElementById('detalles_prueba_paciente');

        const updateVisibility = () => {
            if (detallesPrueba) {
                detallesPrueba.style.display = tienePruebaCheckbox.checked ? 'block' : 'none';
            }
        };

        updateVisibility();
        tienePruebaCheckbox.addEventListener('change', updateVisibility);
    }

    /**
     * Configurar auto-guardado
     */
    setupAutoSave() {
        const inputs = document.querySelectorAll('#trialSection input, #trialSection select, #trialSection textarea');

        inputs.forEach(input => {
            input.addEventListener('change', () => {
                this.updateElectroacousticPreviews();
                this.updateREMPreviews();
                this.saveData();
            });

            input.addEventListener('input', () => {
                clearTimeout(this.saveTimeout);
                this.saveTimeout = setTimeout(() => {
                    this.updateElectroacousticPreviews();
                    this.updateREMPreviews();
                    this.saveData();
                }, 500);
            });
        });
    }

    /**
     * Configurar validación
     */
    setupValidation() {
        const numberInputs = document.querySelectorAll('#trialSection input[type="number"]');

        numberInputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
        });
    }

    /**
     * Validar campo individual
     */
    validateField(input) {
        if (input.type === 'number') {
            const value = parseFloat(input.value);
            const min = parseFloat(input.min);
            const max = parseFloat(input.max);

            if (input.value && (isNaN(value) || value < min || value > max)) {
                input.classList.add('field-error');
                this.app.notify(`Valor fuera del rango (${min}-${max})`, 'warning');
                return false;
            } else {
                input.classList.remove('field-error');
                return true;
            }
        }
        return true;
    }

    /**
     * Actualizar previews electroacústicos
     */
    updateElectroacousticPreviews() {
        const data = this.getData();

        if (this.chartViews.electroacoustic) {
            this.chartViews.electroacoustic.render(data.electroacusticas);
        } else {
            this.renderFallbackChart('freqResponseCanvas', 'Respuesta en Frecuencia');
        }

        if (this.chartViews.compression) {
            this.chartViews.compression.render(data.electroacusticas);
        } else {
            this.renderFallbackChart('compressionCanvas', 'Curvas de Compresión');
        }
    }

    /**
     * Actualizar previews REM
     */
    updateREMPreviews() {
        const data = this.getData();

        if (this.chartViews.realEar) {
            this.chartViews.realEar.render(data.rem);
        } else {
            this.renderFallbackChart('reigTargetCanvas', 'REIG vs Target');
            this.renderFallbackChart('rearTargetCanvas', 'REAR vs Target');
        }
    }

    /**
     * Renderizar fallback para gráficos
     */
    renderFallbackChart(canvasId, title) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = '#666';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(`${title}`, canvas.width/2, canvas.height/2 - 10);
        ctx.fillText('(gráfico no disponible)', canvas.width/2, canvas.height/2 + 10);
    }

    /**
     * Guardar datos automáticamente
     */
    saveData() {
        const data = this.getData();
        this.parent.updateSectionData(this.sectionId, data);
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

        const getFrequencyData = (prefix, ear) => {
            const data = {};
            this.frequencies.forEach(freq => {
                const value = getNumberValue(`${prefix}_${ear}_${freq}`);
                if (value !== null) {
                    data[freq] = value;
                }
            });
            return data;
        };

        return {
            // Imágenes (compactas)
            imagenes: this.uploadedImages,

            // Evaluación de uso (simplificada)
            evaluacion_uso: {
                rutina_problemas: getValue('rutina_problemas'),
                situaciones_mantenimiento: getValue('situaciones_mantenimiento')
            },

            // Pruebas electroacústicas
            electroacusticas: {
                ospl90: getNumberValue('ospl90'),
                ganancia_hfa: getNumberValue('ganancia_hfa'),
                thd_500: getNumberValue('thd_500'),
                thd_800: getNumberValue('thd_800'),
                ruido_ein: getNumberValue('ruido_ein'),
                corriente_bateria: getNumberValue('corriente_bateria'),
                respuesta_frecuencia: {
                    oido_derecho: getFrequencyData('freq_response', 'od'),
                    oido_izquierdo: getFrequencyData('freq_response', 'oi')
                },
                compression_ratio: getValue('compression_ratio'),
                knee_point: getNumberValue('knee_point'),
                attack_time: getNumberValue('attack_time'),
                release_time: getNumberValue('release_time')
            },

            // Mediciones REM
            rem: {
                reur_promedio: getNumberValue('reur_promedio'),
                recd_promedio: getNumberValue('recd_promedio'),
                reig: {
                    oido_derecho: getFrequencyData('reig', 'od'),
                    oido_izquierdo: getFrequencyData('reig', 'oi')
                },
                formula_prescriptiva: getValue('formula_prescriptiva'),
                    match_target: getNumberValue('match_target'),
                    desviacion_rms: getNumberValue('desviacion_rms')
            },

            // Algoritmos
            algoritmos: {
                reduccion_ruido: getValue('reduccion_ruido'),
                direccionalidad: getValue('direccionalidad'),
                supresion_feedback: getValue('supresion_feedback'),
                conectividad_bluetooth: getValue('conectividad_bluetooth'),
                observaciones: getValue('observaciones_algoritmos')
            },

            // Prueba del paciente
            tiene_prueba_paciente: document.getElementById('tiene_prueba_paciente')?.checked || false,
            prueba_paciente: document.getElementById('tiene_prueba_paciente')?.checked ? {
                marca_modelo: getValue('prueba_marca_modelo'),
                tiempo_prueba: getValue('tiempo_prueba'),
                satisfaccion_general: getValue('satisfaccion_prueba') ? parseInt(getValue('satisfaccion_prueba')) : null,
                decision_final: getValue('decision_final'),
                comentarios: getValue('comentarios_prueba')
            } : {},

            observaciones: getValue('observaciones_trial')
        };
    }

    /**
     * Validar datos de la sección
     */
    validate(data) {
        const errors = [];

        // Validar rangos electroacústicos
        const electroacousticRanges = {
            ospl90: { min: 90, max: 140 },
            ganancia_hfa: { min: 0, max: 80 },
            thd_500: { min: 0, max: 10 },
            thd_800: { min: 0, max: 10 },
            ruido_ein: { min: 15, max: 35 },
            corriente_bateria: { min: 0.5, max: 5 }
        };

        Object.keys(electroacousticRanges).forEach(field => {
            const value = data.electroacusticas?.[field];
            const range = electroacousticRanges[field];
            if (value !== null && (value < range.min || value > range.max)) {
                errors.push(`${field} debe estar entre ${range.min}-${range.max}`);
            }
        });

        // Si tiene prueba del paciente, validar decisión
        if (data.tiene_prueba_paciente && !data.prueba_paciente?.decision_final) {
            errors.push('Decisión final es requerida cuando se realizó prueba');
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

        // Al menos debe tener evaluación de uso o datos electroacústicos
        const hasEvaluacion = data.evaluacion_uso && (
            data.evaluacion_uso.rutina_problemas ||
            data.evaluacion_uso.situaciones_mantenimiento
        );

        const hasElectroacusticas = data.electroacusticas && (
            data.electroacusticas.ospl90 ||
            data.electroacusticas.ganancia_hfa ||
            Object.keys(data.electroacusticas.respuesta_frecuencia?.oido_derecho || {}).length > 0
        );

        const hasREM = data.rem && (
            data.rem.reur_promedio ||
            Object.keys(data.rem.reig?.oido_derecho || {}).length > 0
        );

        return hasEvaluacion || hasElectroacusticas || hasREM;
    }
}

// Exponer globalmente
window.HearingAidsTrialSection = HearingAidsTrialSection;
