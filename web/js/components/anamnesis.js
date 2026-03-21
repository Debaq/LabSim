/**
 * AnamnesisModule - Historia Clínica y Antecedentes
 */
class AnamnesisModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'anamnesis';
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
            <div class="form-section">
                <h3 class="section-title">📋 Historia Clínica y Anamnesis</h3>
                <p class="section-description">
                    Registro detallado de antecedentes y síntomas actuales del paciente
                </p>

                <!-- Motivo de Consulta -->
                <div class="form-group">
                    <h4 class="section-subtitle">🎯 Motivo de Consulta</h4>
                    <div class="form-row">
                        <div class="form-col-3">
                            <label class="label-required">Síntoma Principal</label>
                            <select id="motivoPrincipal" class="form-control">
                                <option value="">Seleccionar...</option>
                                <option value="hipoacusia">Hipoacusia</option>
                                <option value="tinnitus">Tinnitus</option>
                                <option value="otalgia">Otalgia</option>
                                <option value="otorrea">Otorrea</option>
                                <option value="vertigo">Vértigo</option>
                                <option value="mareos">Mareos</option>
                                <option value="control">Control rutinario</option>
                                <option value="otro">Otro</option>
                            </select>
                        </div>
                        <div class="form-col-3">
                            <label>Severidad</label>
                            <select id="motivoSeveridad" class="form-control">
                                <option value="">No especifica</option>
                                <option value="leve">Leve</option>
                                <option value="moderada">Moderada</option>
                                <option value="severa">Severa</option>
                                <option value="muy_severa">Muy severa</option>
                            </select>
                        </div>
                        <div class="form-col-3">
                            <label>Tiempo de evolución</label>
                            <select id="motivoTiempo" class="form-control">
                                <option value="">No especifica</option>
                                <option value="agudo">Agudo (< 1 mes)</option>
                                <option value="subagudo">Subagudo (1-3 meses)</option>
                                <option value="cronico">Crónico (> 3 meses)</option>
                                <option value="congenito">Congénito</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Descripción adicional</label>
                        <textarea id="motivoDescripcion" placeholder="Descripción en palabras del paciente..." rows="3"></textarea>
                    </div>
                </div>

                <!-- Historia Libre -->
                <div class="form-group">
                    <h4 class="section-subtitle">📝 Historia Libre</h4>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="historiaCooperativo">
                            <label for="historiaCooperativo">Paciente cooperativo</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="historiaOrientado">
                            <label for="historiaOrientado">Orientado en tiempo y espacio</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="historiaConfiable">
                            <label for="historiaConfiable">Relato confiable</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="historiaAcompanado">
                            <label for="historiaAcompanado">Viene acompañado</label>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Observaciones clínicas</label>
                        <textarea id="historiaObservaciones" placeholder="Actitud, comunicación, aspectos relevantes observados..." rows="4"></textarea>
                    </div>
                </div>

                <!-- Antecedentes Mórbidos -->
                <div class="form-group">
                    <h4 class="section-subtitle">🏥 Antecedentes Mórbidos</h4>
                    
                    <div class="antecedentes-container">
                        <div class="antecedentes-disponibles">
                            <h5>Condiciones Disponibles</h5>
                            <div class="drag-source-container" id="antecedentesFuente">
                                <div class="drag-item" draggable="true" data-value="diabetes">
                                    <span class="drag-icon">📊</span> Diabetes
                                </div>
                                <div class="drag-item" draggable="true" data-value="hipertension">
                                    <span class="drag-icon">💓</span> Hipertensión
                                </div>
                                <div class="drag-item" draggable="true" data-value="cardiopatia">
                                    <span class="drag-icon">❤️</span> Cardiopatía
                                </div>
                                <div class="drag-item" draggable="true" data-value="tiroideo">
                                    <span class="drag-icon">🦋</span> Problema tiroideo
                                </div>
                                <div class="drag-item" draggable="true" data-value="renal">
                                    <span class="drag-icon">🫘</span> Enfermedad renal
                                </div>
                                <div class="drag-item" draggable="true" data-value="neurologico">
                                    <span class="drag-icon">🧠</span> Problema neurológico
                                </div>
                                <div class="drag-item" draggable="true" data-value="ototoxicos">
                                    <span class="drag-icon">💊</span> Medicamentos ototóxicos
                                </div>
                                <div class="drag-item" draggable="true" data-value="otitis">
                                    <span class="drag-icon">👂</span> Otitis recurrentes
                                </div>
                                <div class="drag-item" draggable="true" data-value="trauma_craneal">
                                    <span class="drag-icon">🤕</span> Trauma craneal
                                </div>
                                <div class="drag-item" draggable="true" data-value="familiar_hipoacusia">
                                    <span class="drag-icon">👥</span> Antecedente familiar hipoacusia
                                </div>
                            </div>
                        </div>
                        
                        <div class="antecedentes-seleccionados">
                            <h5>Antecedentes del Paciente</h5>
                            <div class="drag-target-container" id="antecedentesSeleccionados">
                                <div class="drop-zone">
                                    <span class="drop-text">Arrastra aquí los antecedentes relevantes</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Exposición a Ruido -->
                <div class="form-group">
                    <h4 class="section-subtitle">🔊 Exposición a Ruido</h4>
                    <div class="form-row">
                        <div class="form-col-2">
                            <label>Exposición ocupacional</label>
                            <select id="ruidoOcupacional" class="form-control">
                                <option value="">No especifica</option>
                                <option value="ninguna">Ninguna</option>
                                <option value="leve">Leve (< 85 dB)</option>
                                <option value="moderada">Moderada (85-95 dB)</option>
                                <option value="severa">Severa (> 95 dB)</option>
                            </select>
                        </div>
                        <div class="form-col-2">
                            <label>Años de exposición</label>
                            <input type="number" id="ruidoAnos" min="0" max="60" placeholder="0">
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-col-2">
                            <label>Uso de protección auditiva</label>
                            <select id="ruidoProteccion" class="form-control">
                                <option value="">No especifica</option>
                                <option value="nunca">Nunca</option>
                                <option value="ocasional">Ocasional</option>
                                <option value="frecuente">Frecuente</option>
                                <option value="sempre">Sempre</option>
                            </select>
                        </div>
                        <div class="form-col-2">
                            <label>Exposición recreacional</label>
                            <select id="ruidoRecreacional" class="form-control">
                                <option value="">No especifica</option>
                                <option value="ninguna">Ninguna</option>
                                <option value="conciertos">Conciertos</option>
                                <option value="disparos">Disparos/Caza</option>
                                <option value="motociclismo">Motociclismo</option>
                                <option value="musica_alta">Música alta frecuente</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Tinnitus -->
                <div class="form-group">
                    <h4 class="section-subtitle">🎵 Tinnitus</h4>
                    <div class="form-row">
                        <div class="form-col-4">
                            <label>Presencia</label>
                            <select id="tinnitusPresencia" class="form-control">
                                <option value="">No evaluado</option>
                                <option value="ausente">Ausente</option>
                                <option value="presente">Presente</option>
                                <option value="no_seguro">No está seguro</option>
                            </select>
                        </div>
                        <div class="form-col-4">
                            <label>Lateralidad</label>
                            <select id="tinnitusLateralidad" class="form-control">
                                <option value="">-</option>
                                <option value="bilateral">Bilateral</option>
                                <option value="oido_derecho">Oído derecho</option>
                                <option value="oido_izquierdo">Oído izquierdo</option>
                                <option value="central">Central</option>
                            </select>
                        </div>
                        <div class="form-col-4">
                            <label>Tipo de sonido</label>
                            <select id="tinnitusTipo" class="form-control">
                                <option value="">-</option>
                                <option value="agudo">Agudo (silbido)</option>
                                <option value="grave">Grave (zumbido)</option>
                                <option value="pulsatil">Pulsátil</option>
                                <option value="multiple">Múltiples tonos</option>
                                <option value="no_tonal">No tonal (ruido)</option>
                            </select>
                        </div>
                        <div class="form-col-4">
                            <label>Severidad (0-10)</label>
                            <input type="range" id="tinnitusSeveridad" min="0" max="10" value="5" class="range-input">
                            <div class="range-value" id="tinnitusSeveridadValue">5</div>
                        </div>
                    </div>
                    
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="tinnitusConstante">
                            <label for="tinnitusConstante">Constante</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="tinnitusIntermitente">
                            <label for="tinnitusIntermitente">Intermitente</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="tinnitusEmpeoraNoche">
                            <label for="tinnitusEmpeoraNoche">Empeora por la noche</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="tinnitusAfectaSueno">
                            <label for="tinnitusAfectaSueno">Afecta el sueño</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="tinnitusAfectaConcentracion">
                            <label for="tinnitusAfectaConcentracion">Afecta concentración</label>
                        </div>
                    </div>
                </div>
            </div>

            <style>
                .antecedentes-container {
                    display: flex;
                    gap: 20px;
                    margin: 20px 0;
                }

                .antecedentes-disponibles,
                .antecedentes-seleccionados {
                    flex: 1;
                    background: #f8f9fa;
                    border: 2px solid #e9ecef;
                    border-radius: 8px;
                    padding: 15px;
                }

                .antecedentes-disponibles h5,
                .antecedentes-seleccionados h5 {
                    margin-bottom: 15px;
                    color: #495057;
                    font-size: 14px;
                    font-weight: 600;
                }

                .drag-source-container,
                .drag-target-container {
                    min-height: 200px;
                }

                .drag-item {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 10px 12px;
                    margin-bottom: 8px;
                    background: white;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    cursor: grab;
                    transition: all 0.2s ease;
                    font-size: 14px;
                }

                .drag-item:hover {
                    border-color: #2a5298;
                    transform: translateY(-1px);
                    box-shadow: 0 2px 8px rgba(42, 82, 152, 0.15);
                }

                .drag-item:active {
                    cursor: grabbing;
                }

                .drag-item.dragging {
                    opacity: 0.5;
                }

                .drag-icon {
                    font-size: 16px;
                }

                .drop-zone {
                    min-height: 180px;
                    border: 2px dashed #dee2e6;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #6c757d;
                    font-style: italic;
                    transition: all 0.3s ease;
                }

                .drop-zone.drag-over {
                    border-color: #2a5298;
                    background-color: rgba(42, 82, 152, 0.05);
                    color: #2a5298;
                }

                .drop-zone.has-items {
                    border-style: solid;
                    background: transparent;
                }

                .dropped-item {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 8px 12px;
                    margin-bottom: 6px;
                    background: #e7f3ff;
                    border: 1px solid #2a5298;
                    border-radius: 6px;
                    font-size: 14px;
                }

                .remove-item {
                    background: none;
                    border: none;
                    color: #dc3545;
                    cursor: pointer;
                    font-size: 16px;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                    transition: background 0.2s ease;
                }

                .remove-item:hover {
                    background: rgba(220, 53, 69, 0.1);
                }

                .range-input {
                    width: 100%;
                    margin: 8px 0 4px 0;
                }

                .range-value {
                    text-align: center;
                    font-weight: 600;
                    color: #2a5298;
                    font-size: 14px;
                }

                @media (max-width: 768px) {
                    .antecedentes-container {
                        flex-direction: column;
                    }
                    
                    .drag-source-container,
                    .drag-target-container {
                        min-height: 150px;
                    }
                }
            </style>
        `;
    }

    /**
     * Inicializar eventos después de renderizar
     */
    initEvents() {
        this.setupDragAndDrop();
        this.setupRangeInputs();
        this.setupFormValidation();
        this.loadExistingData();
    }

    /**
     * Configurar drag and drop
     */
    setupDragAndDrop() {
        const sourceContainer = document.getElementById('antecedentesFuente');
        const targetContainer = document.getElementById('antecedentesSeleccionados');
        const dropZone = targetContainer.querySelector('.drop-zone');

        if (!sourceContainer || !targetContainer) return;

        // Eventos de drag en elementos fuente
        sourceContainer.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('drag-item')) {
                e.target.classList.add('dragging');
                e.dataTransfer.setData('text/plain', e.target.dataset.value);
                e.dataTransfer.setData('text/html', e.target.innerHTML);
            }
        });

        sourceContainer.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('drag-item')) {
                e.target.classList.remove('dragging');
            }
        });

        // Eventos de drop en zona objetivo
        targetContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        targetContainer.addEventListener('dragleave', (e) => {
            if (!targetContainer.contains(e.relatedTarget)) {
                dropZone.classList.remove('drag-over');
            }
        });

        targetContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');

            const value = e.dataTransfer.getData('text/plain');
            const html = e.dataTransfer.getData('text/html');

            if (value && !this.isAntecedenteSelected(value)) {
                this.addAntecedente(value, html);
            }
        });
    }

    /**
     * Verificar si un antecedente ya está seleccionado
     */
    isAntecedenteSelected(value) {
        const targetContainer = document.getElementById('antecedentesSeleccionados');
        return targetContainer.querySelector(`[data-antecedente="${value}"]`) !== null;
    }

    /**
     * Agregar antecedente seleccionado
     */
    addAntecedente(value, html) {
        const targetContainer = document.getElementById('antecedentesSeleccionados');
        const dropZone = targetContainer.querySelector('.drop-zone');

        if (dropZone.classList.contains('has-items')) {
            const newItem = document.createElement('div');
            newItem.className = 'dropped-item';
            newItem.dataset.antecedente = value;
            newItem.innerHTML = `
                <span>${html}</span>
                <button class="remove-item" onclick="this.parentElement.remove(); labSimApp.modules.get('anamnesis').updateDropZone()">×</button>
            `;
            dropZone.appendChild(newItem);
        } else {
            dropZone.innerHTML = '';
            dropZone.classList.add('has-items');
            
            const newItem = document.createElement('div');
            newItem.className = 'dropped-item';
            newItem.dataset.antecedente = value;
            newItem.innerHTML = `
                <span>${html}</span>
                <button class="remove-item" onclick="this.parentElement.remove(); labSimApp.modules.get('anamnesis').updateDropZone()">×</button>
            `;
            dropZone.appendChild(newItem);
        }
    }

    /**
     * Actualizar zona de drop cuando se remueven elementos
     */
    updateDropZone() {
        const dropZone = document.querySelector('#antecedentesSeleccionados .drop-zone');
        const items = dropZone.querySelectorAll('.dropped-item');
        
        if (items.length === 0) {
            dropZone.classList.remove('has-items');
            dropZone.innerHTML = '<span class="drop-text">Arrastra aquí los antecedentes relevantes</span>';
        }
    }

    /**
     * Configurar inputs de rango
     */
    setupRangeInputs() {
        const severidadRange = document.getElementById('tinnitusSeveridad');
        const severidadValue = document.getElementById('tinnitusSeveridadValue');

        if (severidadRange && severidadValue) {
            severidadRange.addEventListener('input', (e) => {
                severidadValue.textContent = e.target.value;
            });
        }
    }

    /**
     * Configurar validación del formulario
     */
    setupFormValidation() {
        // Validación en tiempo real opcional
        const requiredFields = ['motivoPrincipal'];
        
        requiredFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('change', () => {
                    this.validateField(field);
                });
            }
        });
    }

    /**
     * Validar campo individual
     */
    validateField(field) {
        const isValid = field.value.trim() !== '';
        
        if (isValid) {
            field.classList.remove('field-error');
            field.classList.add('field-success');
        } else {
            field.classList.remove('field-success');
            field.classList.add('field-error');
        }
        
        return isValid;
    }

    /**
     * Cargar datos existentes
     */
    loadExistingData() {
        const existingData = this.app.getModuleData(this.moduleId);
        
        if (existingData && Object.keys(existingData).length > 0) {
            // Cargar datos del formulario
            Object.keys(existingData).forEach(section => {
                if (typeof existingData[section] === 'object') {
                    Object.keys(existingData[section]).forEach(key => {
                        const element = document.getElementById(key);
                        if (element) {
                            if (element.type === 'checkbox') {
                                element.checked = existingData[section][key];
                            } else {
                                element.value = existingData[section][key];
                            }
                        }
                    });
                }
            });

            // Cargar antecedentes seleccionados
            if (existingData.antecedentes_morbidos && existingData.antecedentes_morbidos.condiciones) {
                existingData.antecedentes_morbidos.condiciones.forEach(condicion => {
                    const sourceItem = document.querySelector(`[data-value="${condicion}"]`);
                    if (sourceItem) {
                        this.addAntecedente(condicion, sourceItem.innerHTML);
                    }
                });
            }

            // Actualizar range input
            const severidadRange = document.getElementById('tinnitusSeveridad');
            const severidadValue = document.getElementById('tinnitusSeveridadValue');
            if (existingData.tinnitus && existingData.tinnitus.severidad !== undefined) {
                severidadRange.value = existingData.tinnitus.severidad;
                severidadValue.textContent = existingData.tinnitus.severidad;
            }
        }
    }

    /**
     * Obtener datos del formulario
     */
    getData() {
        // Obtener antecedentes seleccionados
        const antecedentesSeleccionados = Array.from(
            document.querySelectorAll('#antecedentesSeleccionados .dropped-item')
        ).map(item => item.dataset.antecedente);

        return {
            motivo_consulta: {
                sintoma_principal: document.getElementById('motivoPrincipal')?.value || '',
                severidad: document.getElementById('motivoSeveridad')?.value || '',
                tiempo_evolucion: document.getElementById('motivoTiempo')?.value || '',
                descripcion: document.getElementById('motivoDescripcion')?.value || ''
            },
            historia_libre: {
                cooperativo: document.getElementById('historiaCooperativo')?.checked || false,
                orientado: document.getElementById('historiaOrientado')?.checked || false,
                confiable: document.getElementById('historiaConfiable')?.checked || false,
                acompanado: document.getElementById('historiaAcompanado')?.checked || false,
                observaciones: document.getElementById('historiaObservaciones')?.value || ''
            },
            antecedentes_morbidos: {
                condiciones: antecedentesSeleccionados
            },
            exposicion_ruido: {
                ocupacional: document.getElementById('ruidoOcupacional')?.value || '',
                anos_exposicion: parseInt(document.getElementById('ruidoAnos')?.value) || 0,
                proteccion_auditiva: document.getElementById('ruidoProteccion')?.value || '',
                recreacional: document.getElementById('ruidoRecreacional')?.value || ''
            },
            tinnitus: {
                presencia: document.getElementById('tinnitusPresencia')?.value || '',
                lateralidad: document.getElementById('tinnitusLateralidad')?.value || '',
                tipo: document.getElementById('tinnitusTipo')?.value || '',
                severidad: parseInt(document.getElementById('tinnitusSeveridad')?.value) || 0,
                constante: document.getElementById('tinnitusConstante')?.checked || false,
                intermitente: document.getElementById('tinnitusIntermitente')?.checked || false,
                empeora_noche: document.getElementById('tinnitusEmpeoraNoche')?.checked || false,
                afecta_sueno: document.getElementById('tinnitusAfectaSueno')?.checked || false,
                afecta_concentracion: document.getElementById('tinnitusAfectaConcentracion')?.checked || false
            }
        };
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        const errors = [];

        // Validar motivo de consulta
        if (!data.motivo_consulta?.sintoma_principal) {
            errors.push('Debe especificar el síntoma principal de consulta');
        }

        // Validar presencia de tinnitus si se seleccionó presente
        if (data.tinnitus?.presencia === 'presente') {
            if (!data.tinnitus.lateralidad) {
                errors.push('Debe especificar la lateralidad del tinnitus');
            }
            if (!data.tinnitus.tipo) {
                errors.push('Debe especificar el tipo de tinnitus');
            }
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
        return data && 
               data.motivo_consulta?.sintoma_principal &&
               (data.antecedentes_morbidos?.condiciones?.length > 0 || true) && // Antecedentes son opcionales
               data.exposicion_ruido &&
               data.tinnitus?.presencia;
    }
}

window.AnamnesisModule = AnamnesisModule;
