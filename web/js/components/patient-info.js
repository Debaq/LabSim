/**
 * PatientInfoModule - Información Básica del Paciente
 */
class PatientInfoModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'patient-info';
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
            <div class="form-section">
                <h3 class="section-title">👤 Información Básica del Paciente</h3>
                <p class="section-description">
                    Complete los datos demográficos básicos y configure el perfil de personalidad para la simulación IA.
                </p>

                <!-- Datos Demográficos -->
                <div class="form-row">
                    <div class="form-col">
                        <label for="nombre" class="label-required">Nombre del Paciente</label>
                        <input type="text" id="nombre" name="nombre" 
                               value="${existingData.nombre || ''}" 
                               placeholder="Ej: María González"
                               required>
                    </div>
                    <div class="form-col-4">
                        <label for="edad" class="label-required">Edad</label>
                        <input type="number" id="edad" name="edad" 
                               min="0" max="120"
                               value="${existingData.edad || ''}" 
                               placeholder="25"
                               required>
                    </div>
                    <div class="form-col-4">
                        <label for="genero" class="label-required">Género</label>
                        <select id="genero" name="genero" required>
                            <option value="">Seleccionar...</option>
                            <option value="M" ${existingData.genero === 'M' ? 'selected' : ''}>Masculino</option>
                            <option value="F" ${existingData.genero === 'F' ? 'selected' : ''}>Femenino</option>
                        </select>
                    </div>
                </div>

                <!-- Perfil de Personalidad IA -->
                <h4 class="section-subtitle">🤖 Perfil de Personalidad IA</h4>
                <p class="section-description">
                    Configure cómo se comportará el paciente virtual durante las pruebas audiológicas.
                </p>

                <div class="form-row">
                    <div class="form-col">
                        <label for="cooperacion">Nivel de Cooperación</label>
                        <div class="form-group">
                            <input type="range" id="cooperacion" name="cooperacion" 
                                   min="0" max="1" step="0.1"
                                   value="${existingData.cooperacion || 0.8}">
                            <div class="range-labels">
                                <span>Poco cooperativo (0.0)</span>
                                <span id="cooperacion-value">${existingData.cooperacion || 0.8}</span>
                                <span>Muy cooperativo (1.0)</span>
                            </div>
                        </div>
                    </div>
                    <div class="form-col">
                        <label for="ansiedad">Nivel de Ansiedad</label>
                        <div class="form-group">
                            <input type="range" id="ansiedad" name="ansiedad" 
                                   min="0" max="1" step="0.1"
                                   value="${existingData.ansiedad || 0.6}">
                            <div class="range-labels">
                                <span>Relajado (0.0)</span>
                                <span id="ansiedad-value">${existingData.ansiedad || 0.6}</span>
                                <span>Muy ansioso (1.0)</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Patrones de Respuesta -->
                <h4 class="section-subtitle">⚡ Patrones de Respuesta</h4>
                
                <div class="form-row">
                    <div class="form-col">
                        <label for="tiempo_respuesta">Tiempo de Respuesta Promedio (ms)</label>
                        <input type="number" id="tiempo_respuesta" name="tiempo_respuesta" 
                               min="200" max="3000" step="50"
                               value="${existingData.tiempo_respuesta_ms || 800}" 
                               placeholder="800">
                        <small class="form-text">Tiempo entre estímulo y respuesta (200-3000 ms)</small>
                    </div>
                    <div class="form-col">
                        <label for="falsos_positivos">Tasa de Falsos Positivos</label>
                        <div class="form-group">
                            <input type="range" id="falsos_positivos" name="falsos_positivos" 
                                   min="0" max="0.5" step="0.05"
                                   value="${existingData.falsos_positivos || 0.15}">
                            <div class="range-labels">
                                <span>0%</span>
                                <span id="falsos-positivos-value">${Math.round((existingData.falsos_positivos || 0.15) * 100)}%</span>
                                <span>50%</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Diagnóstico Sugerido -->
                <h4 class="section-subtitle">🩺 Perfil Patológico</h4>
                
                <div class="form-group">
                    <label for="tipo_patologia" class="label-optional">Tipo de Patología (opcional)</label>
                    <select id="tipo_patologia" name="tipo_patologia">
                        <option value="">Normal / Sin patología específica</option>
                        <option value="hipoacusia_conductiva" ${existingData.tipo_patologia === 'hipoacusia_conductiva' ? 'selected' : ''}>Hipoacusia Conductiva</option>
                        <option value="hipoacusia_neurosensorial" ${existingData.tipo_patologia === 'hipoacusia_neurosensorial' ? 'selected' : ''}>Hipoacusia Neurosensorial</option>
                        <option value="hipoacusia_mixta" ${existingData.tipo_patologia === 'hipoacusia_mixta' ? 'selected' : ''}>Hipoacusia Mixta</option>
                        <option value="presbiacusia" ${existingData.tipo_patologia === 'presbiacusia' ? 'selected' : ''}>Presbiacusia</option>
                        <option value="trauma_acustico" ${existingData.tipo_patologia === 'trauma_acustico' ? 'selected' : ''}>Trauma Acústico</option>
                        <option value="otosclerosis" ${existingData.tipo_patologia === 'otosclerosis' ? 'selected' : ''}>Otosclerosis</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="severidad" class="label-optional">Severidad (opcional)</label>
                    <select id="severidad" name="severidad">
                        <option value="">No especificada</option>
                        <option value="leve" ${existingData.severidad === 'leve' ? 'selected' : ''}>Leve (26-40 dB HL)</option>
                        <option value="moderada" ${existingData.severidad === 'moderada' ? 'selected' : ''}>Moderada (41-70 dB HL)</option>
                        <option value="severa" ${existingData.severidad === 'severa' ? 'selected' : ''}>Severa (71-90 dB HL)</option>
                        <option value="profunda" ${existingData.severidad === 'profunda' ? 'selected' : ''}>Profunda (>90 dB HL)</option>
                    </select>
                </div>

                <!-- Resumen del Perfil -->
                <div class="alert alert-info">
                    <div class="alert-icon">💡</div>
                    <div class="alert-content">
                        <div class="title">Perfil de Simulación</div>
                        <div class="message" id="perfil-resumen">
                            Configure los parámetros para ver el resumen del perfil IA.
                        </div>
                    </div>
                </div>
            </div>

            <style>
                .range-labels {
                    display: flex;
                    justify-content: space-between;
                    font-size: 12px;
                    color: #666;
                    margin-top: 5px;
                }
                .range-labels span:nth-child(2) {
                    font-weight: bold;
                    color: #2a5298;
                }
                .form-text {
                    color: #6c757d;
                    font-size: 12px;
                    margin-top: 4px;
                    display: block;
                }
            </style>
        `;
    }

    /**
     * Inicializar eventos después de renderizar
     */
    initEvents() {
        // Actualizar valores de los rangesliders
        const cooperacion = document.getElementById('cooperacion');
        const ansiedad = document.getElementById('ansiedad');
        const falsoPositivos = document.getElementById('falsos_positivos');

        if (cooperacion) {
            cooperacion.addEventListener('input', (e) => {
                document.getElementById('cooperacion-value').textContent = e.target.value;
                this.updateProfileSummary();
            });
        }

        if (ansiedad) {
            ansiedad.addEventListener('input', (e) => {
                document.getElementById('ansiedad-value').textContent = e.target.value;
                this.updateProfileSummary();
            });
        }

        if (falsoPositivos) {
            falsoPositivos.addEventListener('input', (e) => {
                const percentage = Math.round(e.target.value * 100);
                document.getElementById('falsos-positivos-value').textContent = `${percentage}%`;
                this.updateProfileSummary();
            });
        }

        // Actualizar resumen cuando cambien otros campos
        const campos = ['nombre', 'edad', 'genero', 'tipo_patologia', 'severidad', 'tiempo_respuesta'];
        campos.forEach(campo => {
            const elemento = document.getElementById(campo);
            if (elemento) {
                elemento.addEventListener('change', () => this.updateProfileSummary());
            }
        });

        // Actualizar resumen inicial
        this.updateProfileSummary();
    }

    /**
     * Actualizar resumen del perfil
     */
    updateProfileSummary() {
        const data = this.getData();
        const resumen = document.getElementById('perfil-resumen');
        
        if (!resumen) return;

        if (!data.nombre || !data.edad || !data.genero) {
            resumen.textContent = 'Complete los datos básicos para ver el resumen del perfil.';
            return;
        }

        const cooperacionDesc = data.cooperacion >= 0.7 ? 'cooperativo' : data.cooperacion >= 0.4 ? 'moderadamente cooperativo' : 'poco cooperativo';
        const ansiedadDesc = data.ansiedad >= 0.7 ? 'ansioso' : data.ansiedad >= 0.4 ? 'moderadamente ansioso' : 'relajado';
        const velocidadDesc = data.tiempo_respuesta_ms <= 600 ? 'respuestas rápidas' : data.tiempo_respuesta_ms <= 1000 ? 'respuestas normales' : 'respuestas lentas';
        
        let patologiaDesc = '';
        if (data.tipo_patologia && data.severidad) {
            patologiaDesc = ` con ${data.tipo_patologia.replace(/_/g, ' ')} ${data.severidad}`;
        } else if (data.tipo_patologia) {
            patologiaDesc = ` con ${data.tipo_patologia.replace(/_/g, ' ')}`;
        }

        resumen.textContent = `Paciente ${cooperacionDesc} y ${ansiedadDesc}, con ${velocidadDesc} (${data.tiempo_respuesta_ms}ms) y ${Math.round(data.falsos_positivos * 100)}% de falsos positivos${patologiaDesc}.`;
    }

    /**
     * Obtener datos del formulario
     */
    getData() {
        const getData = (id, defaultValue = '') => {
            const element = document.getElementById(id);
            return element ? element.value : defaultValue;
        };

        const getNumericData = (id, defaultValue = null) => {
            const element = document.getElementById(id);
            const value = element ? parseFloat(element.value) : defaultValue;
            return isNaN(value) ? defaultValue : value;
        };

        return {
            // Datos demográficos
            nombre: getData('nombre'),
            edad: getNumericData('edad'),
            genero: getData('genero'),
            
            // Perfil de personalidad IA
            cooperacion: getNumericData('cooperacion', 0.8),
            ansiedad: getNumericData('ansiedad', 0.6),
            
            // Patrones de respuesta
            tiempo_respuesta_ms: getNumericData('tiempo_respuesta', 800),
            falsos_positivos: getNumericData('falsos_positivos', 0.15),
            
            // Perfil patológico
            tipo_patologia: getData('tipo_patologia'),
            severidad: getData('severidad')
        };
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        const errors = [];

        // Validaciones requeridas
        if (!data.nombre || data.nombre.trim().length < 2) {
            errors.push('El nombre debe tener al menos 2 caracteres');
        }

        if (!data.edad || data.edad < 0 || data.edad > 120) {
            errors.push('La edad debe estar entre 0 y 120 años');
        }

        if (!data.genero || !['M', 'F'].includes(data.genero)) {
            errors.push('Debe seleccionar un género válido');
        }

        // Validaciones de rangos
        if (data.cooperacion < 0 || data.cooperacion > 1) {
            errors.push('El nivel de cooperación debe estar entre 0 y 1');
        }

        if (data.ansiedad < 0 || data.ansiedad > 1) {
            errors.push('El nivel de ansiedad debe estar entre 0 y 1');
        }

        if (data.tiempo_respuesta_ms < 200 || data.tiempo_respuesta_ms > 3000) {
            errors.push('El tiempo de respuesta debe estar entre 200 y 3000 ms');
        }

        if (data.falsos_positivos < 0 || data.falsos_positivos > 0.5) {
            errors.push('La tasa de falsos positivos debe estar entre 0% y 50%');
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    /**
     * Verificar si está completosasddsa
     */
    isComplete(data) {
        return data && 
               data.nombre && 
               data.edad && 
               data.genero &&
               data.cooperacion !== undefined &&
               data.ansiedad !== undefined &&
               data.tiempo_respuesta_ms !== undefined &&
               data.falsos_positivos !== undefined;
    }
}
window.PatientInfoModule = PatientInfoModule;
