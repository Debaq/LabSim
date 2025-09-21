/**
 * HearingAidsHistorySection - Sección de Historial de Audífonos
 * Información básica, experiencia del usuario, problemas y expectativas
 */

class HearingAidsHistorySection {
    constructor(app, parentModule) {
        this.app = app;
        this.parent = parentModule;
        this.sectionId = 'history';
    }

    /**
     * Renderizar contenido de la sección
     */
    async render(existingData = {}) {
        return `
            <div class="aids-history-content">
                <!-- Información Básica -->
                <div class="form-group">
                    <h4 class="section-subtitle">📋 Información Básica</h4>
                    
                    <div class="form-row">
                        <div class="form-col-3">
                            <label class="label-required">Uso Previo</label>
                            <select id="uso_previo" tabindex="1">
                                <option value="">Seleccionar...</option>
                                <option value="primera_vez" ${this.getSelected(existingData.uso_previo, 'primera_vez')}>Primera vez</option>
                                <option value="si_anterior" ${this.getSelected(existingData.uso_previo, 'si_anterior')}>Sí, ha usado antes</option>
                                <option value="no_actual" ${this.getSelected(existingData.uso_previo, 'no_actual')}>No usa actualmente</option>
                            </select>
                        </div>
                        
                        <div class="form-col-3">
                            <label class="label-optional">Años de Experiencia</label>
                            <select id="anos_experiencia" tabindex="2">
                                <option value="">No aplica</option>
                                <option value="0" ${this.getSelected(existingData.anos_experiencia, '0')}>0 años</option>
                                <option value="1-3" ${this.getSelected(existingData.anos_experiencia, '1-3')}>1-3 años</option>
                                <option value="4-10" ${this.getSelected(existingData.anos_experiencia, '4-10')}>4-10 años</option>
                                <option value=">10" ${this.getSelected(existingData.anos_experiencia, '>10')}>>10 años</option>
                            </select>
                        </div>
                        
                        <div class="form-col-3">
                            <label class="label-optional">Adaptación</label>
                            <select id="adaptacion_tipo" tabindex="3">
                                <option value="">No aplica</option>
                                <option value="unilateral" ${this.getSelected(existingData.adaptacion_tipo, 'unilateral')}>Unilateral</option>
                                <option value="bilateral" ${this.getSelected(existingData.adaptacion_tipo, 'bilateral')}>Bilateral</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Audífonos Anteriores -->
                <div class="form-group" id="audifonos_anteriores_group" style="display: none;">
                    <h4 class="section-subtitle">🎧 Audífonos Anteriores</h4>
                    
                    <div class="form-row">
                        <div class="form-col-3">
                            <label>Tipo/Estilo</label>
                            <select id="tipo_anterior" tabindex="4">
                                <option value="">Seleccionar...</option>
                                <option value="bte" ${this.getSelected(existingData.tipo_anterior, 'bte')}>BTE (Detrás del oído)</option>
                                <option value="ric_rite" ${this.getSelected(existingData.tipo_anterior, 'ric_rite')}>RIC/RITE (Receptor en canal)</option>
                                <option value="ite" ${this.getSelected(existingData.tipo_anterior, 'ite')}>ITE (En el oído)</option>
                                <option value="itc" ${this.getSelected(existingData.tipo_anterior, 'itc')}>ITC (En el canal)</option>
                                <option value="cic" ${this.getSelected(existingData.tipo_anterior, 'cic')}>CIC (Completamente en canal)</option>
                                <option value="iic" ${this.getSelected(existingData.tipo_anterior, 'iic')}>IIC (Invisible en canal)</option>
                                <option value="cros" ${this.getSelected(existingData.tipo_anterior, 'cros')}>CROS</option>
                                <option value="bicros" ${this.getSelected(existingData.tipo_anterior, 'bicros')}>BiCROS</option>
                                <option value="implante_oseo" ${this.getSelected(existingData.tipo_anterior, 'implante_oseo')}>Implante conducción ósea</option>
                            </select>
                        </div>
                        
                        <div class="form-col-3">
                            <label>Tecnología</label>
                            <select id="tecnologia_anterior" tabindex="5">
                                <option value="">Seleccionar...</option>
                                <option value="analogo" ${this.getSelected(existingData.tecnologia_anterior, 'analogo')}>Análogo</option>
                                <option value="digital_programable" ${this.getSelected(existingData.tecnologia_anterior, 'digital_programable')}>Digital programable</option>
                                <option value="digital_basico" ${this.getSelected(existingData.tecnologia_anterior, 'digital_basico')}>Digital básico</option>
                                <option value="digital_ia" ${this.getSelected(existingData.tecnologia_anterior, 'digital_ia')}>Digital con IA</option>
                                <option value="digital_conectividad" ${this.getSelected(existingData.tecnologia_anterior, 'digital_conectividad')}>Digital conectividad avanzada</option>
                            </select>
                        </div>
                        
                        <div class="form-col-3">
                            <label>Gama/Nivel</label>
                            <select id="gama_anterior" tabindex="6">
                                <option value="">Seleccionar...</option>
                                <option value="basico" ${this.getSelected(existingData.gama_anterior, 'basico')}>Básico (4-8 canales)</option>
                                <option value="intermedio" ${this.getSelected(existingData.gama_anterior, 'intermedio')}>Intermedio (12-16 canales)</option>
                                <option value="avanzado" ${this.getSelected(existingData.gama_anterior, 'avanzado')}>Avanzado (20+ canales)</option>
                                <option value="premium" ${this.getSelected(existingData.gama_anterior, 'premium')}>Premium (funciones completas)</option>
                            </select>
                        </div>
                    </div>

                    <!-- Características Técnicas -->
                    <div class="form-group">
                        <label>Características Técnicas</label>
                        <div class="checkbox-group">
                            ${this.renderCharacteristicsCheckboxes(existingData.caracteristicas_anteriores)}
                        </div>
                    </div>
                </div>

                <!-- Experiencia del Usuario -->
                <div class="form-group" id="experiencia_usuario_group" style="display: none;">
                    <h4 class="section-subtitle">👤 Experiencia del Usuario</h4>
                    
                    <div class="form-row">
                        <div class="form-col-4">
                            <label>Nivel de Uso Diario</label>
                            <select id="uso_diario" tabindex="15">
                                <option value="">Seleccionar...</option>
                                <option value="no_usa" ${this.getSelected(existingData.uso_diario, 'no_usa')}>No usa</option>
                                <option value="menos_4h" ${this.getSelected(existingData.uso_diario, 'menos_4h')}><4 horas</option>
                                <option value="4_8h" ${this.getSelected(existingData.uso_diario, '4_8h')}>4-8 horas</option>
                                <option value="mas_8h" ${this.getSelected(existingData.uso_diario, 'mas_8h')}>>8 horas</option>
                            </select>
                        </div>
                        
                        <div class="form-col-4">
                            <label>Satisfacción General</label>
                            <select id="satisfaccion" tabindex="16">
                                <option value="">Seleccionar...</option>
                                ${this.renderSatisfactionOptions(existingData.satisfaccion)}
                            </select>
                        </div>
                        
                        <div class="form-col-4">
                            <label>Compliance</label>
                            <select id="compliance" tabindex="17">
                                <option value="">Seleccionar...</option>
                                <option value="excelente" ${this.getSelected(existingData.compliance, 'excelente')}>Excelente</option>
                                <option value="buena" ${this.getSelected(existingData.compliance, 'buena')}>Buena</option>
                                <option value="regular" ${this.getSelected(existingData.compliance, 'regular')}>Regular</option>
                                <option value="mala" ${this.getSelected(existingData.compliance, 'mala')}>Mala</option>
                            </select>
                        </div>
                        
                        <div class="form-col-4">
                            <label class="label-required">Razón de Consulta</label>
                            <select id="razon_consulta" tabindex="18">
                                <option value="">Seleccionar...</option>
                                <option value="primera_adaptacion" ${this.getSelected(existingData.razon_consulta, 'primera_adaptacion')}>Primera adaptación</option>
                                <option value="renovacion" ${this.getSelected(existingData.razon_consulta, 'renovacion')}>Renovación</option>
                                <option value="problemas" ${this.getSelected(existingData.razon_consulta, 'problemas')}>Problemas</option>
                                <option value="perdida" ${this.getSelected(existingData.razon_consulta, 'perdida')}>Pérdida</option>
                                <option value="seguimiento" ${this.getSelected(existingData.razon_consulta, 'seguimiento')}>Seguimiento</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Problemas Reportados -->
                <div class="form-group" id="problemas_group" style="display: none;">
                    <h4 class="section-subtitle">⚠️ Problemas Reportados</h4>
                    <div class="checkbox-group">
                        ${this.renderProblemsCheckboxes(existingData.problemas_reportados)}
                    </div>
                </div>

                <!-- Expectativas Actuales -->
                <div class="form-group">
                    <h4 class="section-subtitle">🎯 Expectativas Actuales</h4>
                    
                    <div class="form-row">
                        <div class="form-col-4">
                            <label class="label-required">Motivación</label>
                            <select id="motivacion" tabindex="25">
                                <option value="">Seleccionar...</option>
                                <option value="alta" ${this.getSelected(existingData.motivacion, 'alta')}>Alta</option>
                                <option value="media" ${this.getSelected(existingData.motivacion, 'media')}>Media</option>
                                <option value="baja" ${this.getSelected(existingData.motivacion, 'baja')}>Baja</option>
                                <option value="familiar_insiste" ${this.getSelected(existingData.motivacion, 'familiar_insiste')}>Familiar insiste</option>
                            </select>
                        </div>
                        
                        <div class="form-col-4">
                            <label>Presupuesto</label>
                            <select id="presupuesto" tabindex="26">
                                <option value="">Seleccionar...</option>
                                <option value="basico" ${this.getSelected(existingData.presupuesto, 'basico')}>Básico</option>
                                <option value="intermedio" ${this.getSelected(existingData.presupuesto, 'intermedio')}>Intermedio</option>
                                <option value="premium" ${this.getSelected(existingData.presupuesto, 'premium')}>Premium</option>
                                <option value="sin_limite" ${this.getSelected(existingData.presupuesto, 'sin_limite')}>Sin límite</option>
                            </select>
                        </div>
                        
                        <div class="form-col-2">
                            <label>Prioridades</label>
                            <div class="checkbox-group">
                                ${this.renderPrioritiesCheckboxes(existingData.prioridades)}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Observaciones -->
                <div class="form-group">
                    <label class="label-optional">Observaciones Adicionales</label>
                    <textarea id="observaciones_historial" 
                              rows="3" 
                              tabindex="32"
                              placeholder="Información adicional sobre el historial de audífonos...">${existingData.observaciones || ''}</textarea>
                </div>
            </div>

            <style>
            .aids-history-content {
                animation: slideIn 0.3s ease-out;
            }

            .section-subtitle {
                color: #2a5298;
                font-size: 1.1em;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 1px solid #e9ecef;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .aids-conditional-section {
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 20px;
                margin-top: 15px;
                transition: all 0.3s ease;
            }

            .aids-conditional-section.visible {
                background: white;
                border-color: #2a5298;
                box-shadow: 0 2px 8px rgba(42, 82, 152, 0.1);
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
     * Renderizar checkboxes de características técnicas
     */
    renderCharacteristicsCheckboxes(selectedItems = []) {
        const characteristics = [
            { id: 'direccionalidad', label: 'Direccionalidad', tabindex: 7 },
            { id: 'reduccion_ruido', label: 'Reducción de ruido', tabindex: 8 },
            { id: 'bluetooth', label: 'Conectividad Bluetooth', tabindex: 9 },
            { id: 'telecoil', label: 'Telecoil', tabindex: 10 },
            { id: 'bateria_recargable', label: 'Batería recargable', tabindex: 11 },
            { id: 'supresion_feedback', label: 'Supresión feedback', tabindex: 12 },
            { id: 'compresion_multicanal', label: 'Compresión multicanal', tabindex: 13 }
        ];

        return characteristics.map(char => `
            <div class="checkbox-item">
                <input type="checkbox" 
                       id="char_${char.id}" 
                       value="${char.id}"
                       tabindex="${char.tabindex}"
                       ${selectedItems.includes(char.id) ? 'checked' : ''}>
                <label for="char_${char.id}">${char.label}</label>
            </div>
        `).join('');
    }

    /**
     * Renderizar opciones de satisfacción (1-10)
     */
    renderSatisfactionOptions(selectedValue) {
        let options = '';
        for (let i = 1; i <= 10; i++) {
            const selected = selectedValue == i ? 'selected' : '';
            options += `<option value="${i}" ${selected}>${i} ${i <= 3 ? '(Muy baja)' : i <= 5 ? '(Baja)' : i <= 7 ? '(Media)' : i <= 9 ? '(Alta)' : '(Excelente)'}</option>`;
        }
        return options;
    }

    /**
     * Renderizar checkboxes de problemas
     */
    renderProblemsCheckboxes(selectedItems = []) {
        const problems = [
            { id: 'feedback', label: 'Feedback/silbidos', tabindex: 19 },
            { id: 'sonido_poco_natural', label: 'Sonido poco natural', tabindex: 20 },
            { id: 'molestias_fisicas', label: 'Molestias físicas', tabindex: 21 },
            { id: 'dificultad_ruido', label: 'Dificultad en ruido', tabindex: 22 },
            { id: 'bateria_agota', label: 'Batería se agota rápido', tabindex: 23 },
            { id: 'pierde_rompe', label: 'Se pierde/rompe frecuentemente', tabindex: 24 }
        ];

        return problems.map(problem => `
            <div class="checkbox-item">
                <input type="checkbox" 
                       id="prob_${problem.id}" 
                       value="${problem.id}"
                       tabindex="${problem.tabindex}"
                       ${selectedItems.includes(problem.id) ? 'checked' : ''}>
                <label for="prob_${problem.id}">${problem.label}</label>
            </div>
        `).join('');
    }

    /**
     * Renderizar checkboxes de prioridades
     */
    renderPrioritiesCheckboxes(selectedItems = []) {
        const priorities = [
            { id: 'conversacion', label: 'Conversación', tabindex: 27 },
            { id: 'tv', label: 'TV', tabindex: 28 },
            { id: 'telefono', label: 'Teléfono', tabindex: 29 },
            { id: 'musica', label: 'Música', tabindex: 30 },
            { id: 'trabajo', label: 'Trabajo', tabindex: 31 }
        ];

        return priorities.map(priority => `
            <div class="checkbox-item">
                <input type="checkbox" 
                       id="prio_${priority.id}" 
                       value="${priority.id}"
                       tabindex="${priority.tabindex}"
                       ${selectedItems.includes(priority.id) ? 'checked' : ''}>
                <label for="prio_${priority.id}">${priority.label}</label>
            </div>
        `).join('');
    }

    /**
     * Inicializar eventos después de renderizar
     */
    async initEvents() {
        // Controlar visibilidad de secciones condicionales
        this.setupConditionalSections();

        // Auto-save al cambiar valores
        this.setupAutoSave();

        // Validación en tiempo real
        this.setupValidation();
    }

    /**
     * Configurar secciones condicionales
     */
    setupConditionalSections() {
        const usoPrevioSelect = document.getElementById('uso_previo');
        if (!usoPrevioSelect) return;

        const conditionalSections = [
            'audifonos_anteriores_group',
            'experiencia_usuario_group', 
            'problemas_group'
        ];

        const updateConditionalVisibility = () => {
            const value = usoPrevioSelect.value;
            const shouldShow = value === 'si_anterior' || value === 'no_actual';

            conditionalSections.forEach(sectionId => {
                const section = document.getElementById(sectionId);
                if (section) {
                    if (shouldShow) {
                        section.style.display = 'block';
                        section.classList.add('aids-conditional-section', 'visible');
                    } else {
                        section.style.display = 'none';
                        section.classList.remove('aids-conditional-section', 'visible');
                    }
                }
            });
        };

        // Configurar al cargar y al cambiar
        updateConditionalVisibility();
        usoPrevioSelect.addEventListener('change', updateConditionalVisibility);
    }

    /**
     * Configurar auto-guardado
     */
    setupAutoSave() {
        const inputs = document.querySelectorAll('#historySection input, #historySection select, #historySection textarea');
        
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                this.saveData();
            });

            // Para checkboxes, también escuchar click
            if (input.type === 'checkbox') {
                input.addEventListener('click', () => {
                    setTimeout(() => this.saveData(), 50);
                });
            }
        });
    }

    /**
     * Configurar validación
     */
    setupValidation() {
        const requiredFields = ['uso_previo', 'razon_consulta', 'motivacion'];
        
        requiredFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('blur', () => {
                    this.validateField(field);
                });
            }
        });
    }

    /**
     * Validar campo individual
     */
    validateField(field) {
        if (field.hasAttribute('required') || field.classList.contains('label-required')) {
            if (!field.value || field.value === '') {
                field.classList.add('field-error');
                return false;
            } else {
                field.classList.remove('field-error');
                return true;
            }
        }
        return true;
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

        const getCheckboxValues = (prefix) => {
            const checkboxes = document.querySelectorAll(`input[type="checkbox"][id^="${prefix}_"]:checked`);
            return Array.from(checkboxes).map(cb => cb.value);
        };

        return {
            uso_previo: getValue('uso_previo'),
            anos_experiencia: getValue('anos_experiencia'),
            adaptacion_tipo: getValue('adaptacion_tipo'),
            tipo_anterior: getValue('tipo_anterior'),
            tecnologia_anterior: getValue('tecnologia_anterior'),
            gama_anterior: getValue('gama_anterior'),
            caracteristicas_anteriores: getCheckboxValues('char'),
            uso_diario: getValue('uso_diario'),
            satisfaccion: getValue('satisfaccion'),
            compliance: getValue('compliance'),
            razon_consulta: getValue('razon_consulta'),
            problemas_reportados: getCheckboxValues('prob'),
            motivacion: getValue('motivacion'),
            presupuesto: getValue('presupuesto'),
            prioridades: getCheckboxValues('prio'),
            observaciones: getValue('observaciones_historial')
        };
    }

    /**
     * Validar datos de la sección
     */
    validate(data) {
        const errors = [];

        // Campos requeridos
        if (!data.uso_previo) {
            errors.push('Uso previo es requerido');
        }

        if (!data.razon_consulta) {
            errors.push('Razón de consulta es requerida');
        }

        if (!data.motivacion) {
            errors.push('Motivación es requerida');
        }

        // Validaciones condicionales
        if ((data.uso_previo === 'si_anterior' || data.uso_previo === 'no_actual')) {
            if (!data.tipo_anterior) {
                errors.push('Tipo de audífono anterior es requerido');
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
        const validation = this.validate(data);
        return validation.isValid;
    }
}

// Exponer globalmente
window.HearingAidsHistorySection = HearingAidsHistorySection;