/**
 * SupraliminalModule - Pruebas Supraliminares
 * Incluye pruebas de deterioro y reclutamiento
 */
class SupraliminalModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'supraliminal';
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
            <div class="form-section">
                <h3 class="section-title">📊 Pruebas Supraliminares</h3>
                <p class="section-description">
                    Evaluación de deterioro auditivo retrococlear y reclutamiento coclear
                </p>

                <!-- Pruebas de Deterioro -->
                <div class="form-section">
                    <h4 class="section-subtitle">🔍 Pruebas de Deterioro</h4>
                    
                    <!-- STAT (Short Increment Sensitivity Index Test) -->
                    <div class="form-group">
                        <label class="label-optional">Prueba STAT (%)</label>
                        <div class="ear-selector">
                            <div class="ear-column">
                                <div class="ear-title">Oído Derecho</div>
                                <div class="frequency-grid">
                                    <div class="frequency-label">500 Hz</div>
                                    <input type="number" id="stat_od_500" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.stat?.od?.['500'] || ''}">
                                    
                                    <div class="frequency-label">1000 Hz</div>
                                    <input type="number" id="stat_od_1000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.stat?.od?.['1000'] || ''}">
                                    
                                    <div class="frequency-label">2000 Hz</div>
                                    <input type="number" id="stat_od_2000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.stat?.od?.['2000'] || ''}">
                                    
                                    <div class="frequency-label">4000 Hz</div>
                                    <input type="number" id="stat_od_4000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.stat?.od?.['4000'] || ''}">
                                </div>
                            </div>
                            <div class="ear-column">
                                <div class="ear-title">Oído Izquierdo</div>
                                <div class="frequency-grid">
                                    <div class="frequency-label">500 Hz</div>
                                    <input type="number" id="stat_oi_500" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.stat?.oi?.['500'] || ''}">
                                    
                                    <div class="frequency-label">1000 Hz</div>
                                    <input type="number" id="stat_oi_1000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.stat?.oi?.['1000'] || ''}">
                                    
                                    <div class="frequency-label">2000 Hz</div>
                                    <input type="number" id="stat_oi_2000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.stat?.oi?.['2000'] || ''}">
                                    
                                    <div class="frequency-label">4000 Hz</div>
                                    <input type="number" id="stat_oi_4000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.stat?.oi?.['4000'] || ''}">
                                </div>
                            </div>
                        </div>
                        <small class="help-text">Normal: &lt;20% | Patológico: &gt;60%</small>
                    </div>

                    <!-- Carhart -->
                    <div class="form-group">
                        <label class="label-optional">Prueba de Carhart (dB)</label>
                        <div class="ear-selector">
                            <div class="ear-column">
                                <div class="ear-title">Oído Derecho</div>
                                <div class="frequency-grid">
                                    <div class="frequency-label">500 Hz</div>
                                    <input type="number" id="carhart_od_500" min="0" max="60" step="5" 
                                           placeholder="dB" value="${existingData.carhart?.od?.['500'] || ''}">
                                    
                                    <div class="frequency-label">1000 Hz</div>
                                    <input type="number" id="carhart_od_1000" min="0" max="60" step="5" 
                                           placeholder="dB" value="${existingData.carhart?.od?.['1000'] || ''}">
                                    
                                    <div class="frequency-label">2000 Hz</div>
                                    <input type="number" id="carhart_od_2000" min="0" max="60" step="5" 
                                           placeholder="dB" value="${existingData.carhart?.od?.['2000'] || ''}">
                                    
                                    <div class="frequency-label">4000 Hz</div>
                                    <input type="number" id="carhart_od_4000" min="0" max="60" step="5" 
                                           placeholder="dB" value="${existingData.carhart?.od?.['4000'] || ''}">
                                </div>
                            </div>
                            <div class="ear-column">
                                <div class="ear-title">Oído Izquierdo</div>
                                <div class="frequency-grid">
                                    <div class="frequency-label">500 Hz</div>
                                    <input type="number" id="carhart_oi_500" min="0" max="60" step="5" 
                                           placeholder="dB" value="${existingData.carhart?.oi?.['500'] || ''}">
                                    
                                    <div class="frequency-label">1000 Hz</div>
                                    <input type="number" id="carhart_oi_1000" min="0" max="60" step="5" 
                                           placeholder="dB" value="${existingData.carhart?.oi?.['1000'] || ''}">
                                    
                                    <div class="frequency-label">2000 Hz</div>
                                    <input type="number" id="carhart_oi_2000" min="0" max="60" step="5" 
                                           placeholder="dB" value="${existingData.carhart?.oi?.['2000'] || ''}">
                                    
                                    <div class="frequency-label">4000 Hz</div>
                                    <input type="number" id="carhart_oi_4000" min="0" max="60" step="5" 
                                           placeholder="dB" value="${existingData.carhart?.oi?.['4000'] || ''}">
                                </div>
                            </div>
                        </div>
                        <small class="help-text">Escotoma de Carhart típico: máximo en 2000 Hz</small>
                    </div>

                    <!-- Maspetiol -->
                    <div class="form-group">
                        <label class="label-optional">Prueba de Maspetiol</label>
                        <div class="form-row">
                            <div class="form-col">
                                <label>Oído Derecho</label>
                                <select id="maspetiol_od" value="${existingData.maspetiol?.od || ''}">
                                    <option value="">Seleccionar resultado</option>
                                    <option value="negativo" ${existingData.maspetiol?.od === 'negativo' ? 'selected' : ''}>Negativo (Normal)</option>
                                    <option value="positivo_tipo1" ${existingData.maspetiol?.od === 'positivo_tipo1' ? 'selected' : ''}>Positivo Tipo I (Conducción)</option>
                                    <option value="positivo_tipo2" ${existingData.maspetiol?.od === 'positivo_tipo2' ? 'selected' : ''}>Positivo Tipo II (Mixta)</option>
                                    <option value="positivo_tipo3" ${existingData.maspetiol?.od === 'positivo_tipo3' ? 'selected' : ''}>Positivo Tipo III (Sensorial)</option>
                                </select>
                            </div>
                            <div class="form-col">
                                <label>Oído Izquierdo</label>
                                <select id="maspetiol_oi" value="${existingData.maspetiol?.oi || ''}">
                                    <option value="">Seleccionar resultado</option>
                                    <option value="negativo" ${existingData.maspetiol?.oi === 'negativo' ? 'selected' : ''}>Negativo (Normal)</option>
                                    <option value="positivo_tipo1" ${existingData.maspetiol?.oi === 'positivo_tipo1' ? 'selected' : ''}>Positivo Tipo I (Conducción)</option>
                                    <option value="positivo_tipo2" ${existingData.maspetiol?.oi === 'positivo_tipo2' ? 'selected' : ''}>Positivo Tipo II (Mixta)</option>
                                    <option value="positivo_tipo3" ${existingData.maspetiol?.oi === 'positivo_tipo3' ? 'selected' : ''}>Positivo Tipo III (Sensorial)</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Pruebas de Reclutamiento -->
                <div class="form-section">
                    <h4 class="section-subtitle">🔊 Pruebas de Reclutamiento</h4>
                    
                    <!-- Fowler ABLB -->
                    <div class="form-group">
                        <label class="label-optional">Fowler ABLB (Alternate Binaural Loudness Balance)</label>
                        <div class="frequency-grid">
                            <div class="frequency-label">Frecuencia</div>
                            <div class="frequency-label">Resultado</div>
                            <div class="frequency-label">Diferencia (dB)</div>
                            
                            <div class="frequency-label">500 Hz</div>
                            <select id="fowler_500_resultado">
                                <option value="">Seleccionar</option>
                                <option value="negativo" ${existingData.fowler?.['500']?.resultado === 'negativo' ? 'selected' : ''}>Negativo</option>
                                <option value="positivo_parcial" ${existingData.fowler?.['500']?.resultado === 'positivo_parcial' ? 'selected' : ''}>Positivo Parcial</option>
                                <option value="positivo_completo" ${existingData.fowler?.['500']?.resultado === 'positivo_completo' ? 'selected' : ''}>Positivo Completo</option>
                            </select>
                            <input type="number" id="fowler_500_diferencia" min="0" max="40" step="5" 
                                   placeholder="dB" value="${existingData.fowler?.['500']?.diferencia || ''}">
                            
                            <div class="frequency-label">1000 Hz</div>
                            <select id="fowler_1000_resultado">
                                <option value="">Seleccionar</option>
                                <option value="negativo" ${existingData.fowler?.['1000']?.resultado === 'negativo' ? 'selected' : ''}>Negativo</option>
                                <option value="positivo_parcial" ${existingData.fowler?.['1000']?.resultado === 'positivo_parcial' ? 'selected' : ''}>Positivo Parcial</option>
                                <option value="positivo_completo" ${existingData.fowler?.['1000']?.resultado === 'positivo_completo' ? 'selected' : ''}>Positivo Completo</option>
                            </select>
                            <input type="number" id="fowler_1000_diferencia" min="0" max="40" step="5" 
                                   placeholder="dB" value="${existingData.fowler?.['1000']?.diferencia || ''}">
                            
                            <div class="frequency-label">2000 Hz</div>
                            <select id="fowler_2000_resultado">
                                <option value="">Seleccionar</option>
                                <option value="negativo" ${existingData.fowler?.['2000']?.resultado === 'negativo' ? 'selected' : ''}>Negativo</option>
                                <option value="positivo_parcial" ${existingData.fowler?.['2000']?.resultado === 'positivo_parcial' ? 'selected' : ''}>Positivo Parcial</option>
                                <option value="positivo_completo" ${existingData.fowler?.['2000']?.resultado === 'positivo_completo' ? 'selected' : ''}>Positivo Completo</option>
                            </select>
                            <input type="number" id="fowler_2000_diferencia" min="0" max="40" step="5" 
                                   placeholder="dB" value="${existingData.fowler?.['2000']?.diferencia || ''}">
                            
                            <div class="frequency-label">4000 Hz</div>
                            <select id="fowler_4000_resultado">
                                <option value="">Seleccionar</option>
                                <option value="negativo" ${existingData.fowler?.['4000']?.resultado === 'negativo' ? 'selected' : ''}>Negativo</option>
                                <option value="positivo_parcial" ${existingData.fowler?.['4000']?.resultado === 'positivo_parcial' ? 'selected' : ''}>Positivo Parcial</option>
                                <option value="positivo_completo" ${existingData.fowler?.['4000']?.resultado === 'positivo_completo' ? 'selected' : ''}>Positivo Completo</option>
                            </select>
                            <input type="number" id="fowler_4000_diferencia" min="0" max="40" step="5" 
                                   placeholder="dB" value="${existingData.fowler?.['4000']?.diferencia || ''}">
                        </div>
                        <small class="help-text">Reclutamiento completo: diferencia &lt;10 dB</small>
                    </div>

                    <!-- SISI -->
                    <div class="form-group">
                        <label class="label-optional">SISI (Short Increment Sensitivity Index) - %</label>
                        <div class="ear-selector">
                            <div class="ear-column">
                                <div class="ear-title">Oído Derecho</div>
                                <div class="frequency-grid">
                                    <div class="frequency-label">500 Hz</div>
                                    <input type="number" id="sisi_od_500" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.sisi?.od?.['500'] || ''}">
                                    
                                    <div class="frequency-label">1000 Hz</div>
                                    <input type="number" id="sisi_od_1000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.sisi?.od?.['1000'] || ''}">
                                    
                                    <div class="frequency-label">2000 Hz</div>
                                    <input type="number" id="sisi_od_2000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.sisi?.od?.['2000'] || ''}">
                                    
                                    <div class="frequency-label">4000 Hz</div>
                                    <input type="number" id="sisi_od_4000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.sisi?.od?.['4000'] || ''}">
                                </div>
                            </div>
                            <div class="ear-column">
                                <div class="ear-title">Oído Izquierdo</div>
                                <div class="frequency-grid">
                                    <div class="frequency-label">500 Hz</div>
                                    <input type="number" id="sisi_oi_500" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.sisi?.oi?.['500'] || ''}">
                                    
                                    <div class="frequency-label">1000 Hz</div>
                                    <input type="number" id="sisi_oi_1000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.sisi?.oi?.['1000'] || ''}">
                                    
                                    <div class="frequency-label">2000 Hz</div>
                                    <input type="number" id="sisi_oi_2000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.sisi?.oi?.['2000'] || ''}">
                                    
                                    <div class="frequency-label">4000 Hz</div>
                                    <input type="number" id="sisi_oi_4000" min="0" max="100" step="5" 
                                           placeholder="%" value="${existingData.sisi?.oi?.['4000'] || ''}">
                                </div>
                            </div>
                        </div>
                        <small class="help-text">Normal: 0-20% | Reclutamiento: 60-100%</small>
                    </div>

                    <!-- Luscher-Zwislocki -->
                    <div class="form-group">
                        <label class="label-optional">Luscher-Zwislocki (Tone Decay)</label>
                        <div class="ear-selector">
                            <div class="ear-column">
                                <div class="ear-title">Oído Derecho</div>
                                <div class="form-row">
                                    <div class="form-col">
                                        <label>500 Hz (seg)</label>
                                        <input type="number" id="luscher_od_500" min="0" max="60" step="5" 
                                               placeholder="segundos" value="${existingData.luscher?.od?.['500'] || ''}">
                                    </div>
                                    <div class="form-col">
                                        <label>1000 Hz (seg)</label>
                                        <input type="number" id="luscher_od_1000" min="0" max="60" step="5" 
                                               placeholder="segundos" value="${existingData.luscher?.od?.['1000'] || ''}">
                                    </div>
                                </div>
                                <div class="form-row">
                                    <div class="form-col">
                                        <label>2000 Hz (seg)</label>
                                        <input type="number" id="luscher_od_2000" min="0" max="60" step="5" 
                                               placeholder="segundos" value="${existingData.luscher?.od?.['2000'] || ''}">
                                    </div>
                                    <div class="form-col">
                                        <label>4000 Hz (seg)</label>
                                        <input type="number" id="luscher_od_4000" min="0" max="60" step="5" 
                                               placeholder="segundos" value="${existingData.luscher?.od?.['4000'] || ''}">
                                    </div>
                                </div>
                            </div>
                            <div class="ear-column">
                                <div class="ear-title">Oído Izquierdo</div>
                                <div class="form-row">
                                    <div class="form-col">
                                        <label>500 Hz (seg)</label>
                                        <input type="number" id="luscher_oi_500" min="0" max="60" step="5" 
                                               placeholder="segundos" value="${existingData.luscher?.oi?.['500'] || ''}">
                                    </div>
                                    <div class="form-col">
                                        <label>1000 Hz (seg)</label>
                                        <input type="number" id="luscher_oi_1000" min="0" max="60" step="5" 
                                               placeholder="segundos" value="${existingData.luscher?.oi?.['1000'] || ''}">
                                    </div>
                                </div>
                                <div class="form-row">
                                    <div class="form-col">
                                        <label>2000 Hz (seg)</label>
                                        <input type="number" id="luscher_oi_2000" min="0" max="60" step="5" 
                                               placeholder="segundos" value="${existingData.luscher?.oi?.['2000'] || ''}">
                                    </div>
                                    <div class="form-col">
                                        <label>4000 Hz (seg)</label>
                                        <input type="number" id="luscher_oi_4000" min="0" max="60" step="5" 
                                               placeholder="segundos" value="${existingData.luscher?.oi?.['4000'] || ''}">
                                    </div>
                                </div>
                            </div>
                        </div>
                        <small class="help-text">Normal: &gt;60 segundos | Patológico: &lt;30 segundos</small>
                    </div>
                </div>

                <!-- Observaciones -->
                <div class="form-group">
                    <label class="label-optional">Observaciones Generales</label>
                    <textarea id="supraliminal_observaciones" rows="3" 
                              placeholder="Comentarios adicionales sobre las pruebas supraliminares...">${existingData.observaciones || ''}</textarea>
                </div>
            </div>
        `;
    }

    /**
     * Inicializar eventos después de renderizar
     */
    initEvents() {
        // Auto-guardado al cambiar cualquier campo
        const container = document.getElementById('tabsContent');
        if (container) {
            container.addEventListener('input', (e) => {
                if (e.target.matches('input, select, textarea')) {
                    const data = this.getData();
                    this.app.updateModuleData(this.moduleId, data);
                }
            });
        }
    }

    /**
     * Obtener datos del formulario
     */
    getData() {
        const data = {
            // Pruebas de deterioro
            stat: {
                od: {
                    '500': this.getInputValue('stat_od_500'),
                    '1000': this.getInputValue('stat_od_1000'),
                    '2000': this.getInputValue('stat_od_2000'),
                    '4000': this.getInputValue('stat_od_4000')
                },
                oi: {
                    '500': this.getInputValue('stat_oi_500'),
                    '1000': this.getInputValue('stat_oi_1000'),
                    '2000': this.getInputValue('stat_oi_2000'),
                    '4000': this.getInputValue('stat_oi_4000')
                }
            },
            carhart: {
                od: {
                    '500': this.getInputValue('carhart_od_500'),
                    '1000': this.getInputValue('carhart_od_1000'),
                    '2000': this.getInputValue('carhart_od_2000'),
                    '4000': this.getInputValue('carhart_od_4000')
                },
                oi: {
                    '500': this.getInputValue('carhart_oi_500'),
                    '1000': this.getInputValue('carhart_oi_1000'),
                    '2000': this.getInputValue('carhart_oi_2000'),
                    '4000': this.getInputValue('carhart_oi_4000')
                }
            },
            maspetiol: {
                od: this.getSelectValue('maspetiol_od'),
                oi: this.getSelectValue('maspetiol_oi')
            },
            // Pruebas de reclutamiento
            fowler: {
                '500': {
                    resultado: this.getSelectValue('fowler_500_resultado'),
                    diferencia: this.getInputValue('fowler_500_diferencia')
                },
                '1000': {
                    resultado: this.getSelectValue('fowler_1000_resultado'),
                    diferencia: this.getInputValue('fowler_1000_diferencia')
                },
                '2000': {
                    resultado: this.getSelectValue('fowler_2000_resultado'),
                    diferencia: this.getInputValue('fowler_2000_diferencia')
                },
                '4000': {
                    resultado: this.getSelectValue('fowler_4000_resultado'),
                    diferencia: this.getInputValue('fowler_4000_diferencia')
                }
            },
            sisi: {
                od: {
                    '500': this.getInputValue('sisi_od_500'),
                    '1000': this.getInputValue('sisi_od_1000'),
                    '2000': this.getInputValue('sisi_od_2000'),
                    '4000': this.getInputValue('sisi_od_4000')
                },
                oi: {
                    '500': this.getInputValue('sisi_oi_500'),
                    '1000': this.getInputValue('sisi_oi_1000'),
                    '2000': this.getInputValue('sisi_oi_2000'),
                    '4000': this.getInputValue('sisi_oi_4000')
                }
            },
            luscher: {
                od: {
                    '500': this.getInputValue('luscher_od_500'),
                    '1000': this.getInputValue('luscher_od_1000'),
                    '2000': this.getInputValue('luscher_od_2000'),
                    '4000': this.getInputValue('luscher_od_4000')
                },
                oi: {
                    '500': this.getInputValue('luscher_oi_500'),
                    '1000': this.getInputValue('luscher_oi_1000'),
                    '2000': this.getInputValue('luscher_oi_2000'),
                    '4000': this.getInputValue('luscher_oi_4000')
                }
            },
            observaciones: this.getTextareaValue('supraliminal_observaciones')
        };

        return data;
    }

    /**
     * Obtener valor de input numérico
     */
    getInputValue(id) {
        const element = document.getElementById(id);
        if (!element || element.value === '') return null;
        const value = parseFloat(element.value);
        return isNaN(value) ? null : value;
    }

    /**
     * Obtener valor de select
     */
    getSelectValue(id) {
        const element = document.getElementById(id);
        return element && element.value !== '' ? element.value : null;
    }

    /**
     * Obtener valor de textarea
     */
    getTextareaValue(id) {
        const element = document.getElementById(id);
        return element && element.value.trim() !== '' ? element.value.trim() : null;
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        const errors = [];

        // Validar rangos STAT (0-100%)
        this.validateRange(data.stat, 'STAT', 0, 100, errors);

        // Validar rangos Carhart (0-60 dB)
        this.validateRange(data.carhart, 'Carhart', 0, 60, errors);

        // Validar rangos SISI (0-100%)
        this.validateRange(data.sisi, 'SISI', 0, 100, errors);

        // Validar rangos Luscher (0-60 segundos)
        this.validateRange(data.luscher, 'Luscher-Zwislocki', 0, 60, errors);

        // Validar Fowler diferencias (0-40 dB)
        if (data.fowler) {
            ['500', '1000', '2000', '4000'].forEach(freq => {
                if (data.fowler[freq]?.diferencia !== null) {
                    const diff = data.fowler[freq].diferencia;
                    if (diff < 0 || diff > 40) {
                        errors.push(`Fowler ${freq}Hz: diferencia debe estar entre 0-40 dB`);
                    }
                }
            });
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    /**
     * Validar rangos de valores
     */
    validateRange(testData, testName, min, max, errors) {
        if (!testData) return;

        ['od', 'oi'].forEach(ear => {
            if (testData[ear]) {
                Object.entries(testData[ear]).forEach(([freq, value]) => {
                    if (value !== null && (value < min || value > max)) {
                        const earName = ear === 'od' ? 'OD' : 'OI';
                        errors.push(`${testName} ${earName} ${freq}Hz: valor debe estar entre ${min}-${max}`);
                    }
                });
            }
        });
    }

    /**
     * Verificar si está completo
     */
    isComplete(data) {
        if (!data) return false;

        // Considerar completo si al menos una prueba tiene datos
        const hasStatData = this.hasTestData(data.stat);
        const hasCarhartData = this.hasTestData(data.carhart);
        const hasMaspetiolData = data.maspetiol?.od || data.maspetiol?.oi;
        const hasFowlerData = this.hasFowlerData(data.fowler);
        const hasSisiData = this.hasTestData(data.sisi);
        const hasLuscherData = this.hasTestData(data.luscher);

        return hasStatData || hasCarhartData || hasMaspetiolData || 
               hasFowlerData || hasSisiData || hasLuscherData;
    }

    /**
     * Verificar si una prueba tiene datos
     */
    hasTestData(testData) {
        if (!testData) return false;

        const odData = testData.od && Object.values(testData.od).some(v => v !== null && v !== undefined);
        const oiData = testData.oi && Object.values(testData.oi).some(v => v !== null && v !== undefined);

        return odData || oiData;
    }

    /**
     * Verificar si Fowler tiene datos
     */
    hasFowlerData(fowlerData) {
        if (!fowlerData) return false;

        return Object.values(fowlerData).some(freq => 
            freq.resultado || freq.diferencia !== null
        );
    }

    /**
     * Verificar si se puede avanzar
     */
    canAdvance() {
        return true; // Módulo opcional, siempre se puede avanzar
    }
}
window.SupraliminalModule = SupraliminalModule;
