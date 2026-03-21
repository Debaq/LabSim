/**
 * AgendaModule - Módulo de Gestión de Agenda
 * Lista de pacientes, creación de agendas y tokens
 */

class AgendaModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'agenda';
        this.patients = [];
        this.agendas = [];
        this.selectedPatient = null;
        this.currentAgenda = null;
        this.apiPassword = 'labsim2024'; // Contraseña hardcodeada
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
        <div class="form-section">
            <h3 class="section-title">📅 Gestión de Agenda</h3>
            <p class="section-description">
                Administra pacientes guardados y crea agendas de atención
            </p>

            <!-- Layout Principal: Pacientes (50%) + Agendas (50%) -->
            <div style="display: flex; gap: 30px;">
                
                <!-- Panel de Pacientes -->
                <div style="flex: 1;">
                    <div class="agenda-section">
                        <h4 class="section-subtitle">👥 Pacientes Guardados</h4>
                        
                        <!-- Controles de pacientes -->
                        <div class="patient-controls">
                            <button class="btn btn-primary" id="refreshPatientsBtn">
                                🔄 Actualizar Lista
                            </button>
                            <button class="btn btn-success" id="uploadPatientBtn" disabled>
                                ⬆️ Subir Paciente Actual
                            </button>
                            <input type="file" id="importJsonFile" accept=".json" style="display: none;">
                            <button class="btn btn-secondary" id="importJsonBtn">
                                📁 Importar JSON
                            </button>
                        </div>

                        <!-- Lista de pacientes -->
                        <div class="patients-list" id="patientsList">
                            <div class="loading-patients">Cargando pacientes...</div>
                        </div>
                    </div>
                </div>

                <!-- Panel de Agendas -->
                <div style="flex: 1;">
                    <div class="agenda-section">
                        <h4 class="section-subtitle">📋 Agendas de Atención</h4>
                        
                        <!-- Controles de agendas -->
                        <div class="agenda-controls">
                            <button class="btn btn-primary" id="createAgendaBtn">
                                ➕ Nueva Agenda
                            </button>
                            <button class="btn btn-warning" id="duplicateAgendaBtn" disabled>
                                📋 Duplicar Agenda
                            </button>
                        </div>

                        <!-- Lista de agendas -->
                        <div class="agendas-list" id="agendasList">
                            <div class="no-agendas">No hay agendas creadas</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Modal para crear/editar agenda -->
            <div class="modal-overlay" id="agendaModal" style="display: none;">
                <div class="modal-content">
                    <h4>📅 Configurar Agenda</h4>
                    
                    <div class="form-group">
                        <label class="label-required">Nombre de la Agenda</label>
                        <input type="text" id="agendaName" placeholder="Ej: Agenda Semanal - Marzo 2025">
                    </div>
                    
                    <div class="form-group">
                        <label class="label-optional">Descripción</label>
                        <textarea id="agendaDescription" rows="2" placeholder="Descripción opcional de la agenda"></textarea>
                    </div>
                    
                    <!-- Slots de horarios -->
                    <div class="agenda-slots">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h5>⏰ Horarios de Atención</h5>
                            <button class="btn btn-success btn-sm" id="addSlotBtn">➕ Agregar Horario</button>
                        </div>
                        <div id="slotsContainer">
                            <!-- Los slots se agregan dinámicamente -->
                        </div>
                    </div>
                    
                    <div class="modal-actions">
                        <button class="btn btn-secondary" id="cancelAgendaBtn">Cancelar</button>
                        <button class="btn btn-primary" id="saveAgendaBtn">Guardar Agenda</button>
                    </div>
                </div>
            </div>

            <!-- Modal para detalles de agenda -->
            <div class="modal-overlay" id="agendaDetailsModal" style="display: none;">
                <div class="modal-content large">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h4 id="agendaDetailsTitle">📅 Detalles de Agenda</h4>
                        <div>
                            <button class="btn btn-warning btn-sm" id="editAgendaBtn">✏️ Editar</button>
                            <button class="btn btn-danger btn-sm" id="deleteAgendaBtn">🗑️ Eliminar</button>
                        </div>
                    </div>
                    
                    <div class="agenda-info">
                        <div class="info-item">
                            <strong>Token de Agenda:</strong>
                            <div class="token-display">
                                <input type="text" id="agendaToken" readonly>
                                <button class="btn btn-sm btn-secondary" id="copyTokenBtn">📋 Copiar</button>
                            </div>
                        </div>
                    </div>
                    
                    <div id="agendaDetailsContent">
                        <!-- Contenido dinámico -->
                    </div>
                    
                    <div class="modal-actions">
                        <button class="btn btn-secondary" id="closeDetailsBtn">Cerrar</button>
                    </div>
                </div>
            </div>
        </div>

        <style>
        .agenda-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #007bff;
            height: 500px;
            display: flex;
            flex-direction: column;
        }

        .patient-controls, .agenda-controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }

        .patients-list, .agendas-list {
            flex: 1;
            overflow-y: auto;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            background: white;
            padding: 10px;
        }

        .patient-item, .agenda-item {
            padding: 12px;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            background: white;
        }

        .patient-item:hover, .agenda-item:hover {
            border-color: #007bff;
            box-shadow: 0 2px 8px rgba(0,123,255,0.1);
        }

        .patient-item.selected, .agenda-item.selected {
            border-color: #007bff;
            background: #e7f3ff;
        }

        .patient-name {
            font-weight: 600;
            color: #2a5298;
            margin-bottom: 4px;
        }

        .patient-info {
            font-size: 12px;
            color: #666;
            display: flex;
            gap: 15px;
        }

        .agenda-name {
            font-weight: 600;
            color: #2a5298;
            margin-bottom: 4px;
        }

        .agenda-info {
            font-size: 12px;
            color: #666;
            margin-bottom: 8px;
        }

        .agenda-token {
            font-family: monospace;
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
        }

        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
        }

        .modal-content {
            background: white;
            border-radius: 12px;
            padding: 25px;
            width: 90%;
            max-width: 500px;
            max-height: 80vh;
            overflow-y: auto;
        }

        .modal-content.large {
            max-width: 700px;
        }

        .modal-actions {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }

        .agenda-slots {
            margin: 20px 0;
        }

        .slot-item {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
        }

        .slot-input {
            padding: 6px 10px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            font-size: 13px;
        }

        .slot-input.date {
            width: 140px;
        }

        .slot-input.time {
            width: 80px;
        }

        .slot-input.duration {
            width: 80px;
        }

        .slot-patient-select {
            flex: 1;
            min-width: 150px;
            padding: 6px 10px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            font-size: 13px;
        }

        .btn-sm {
            padding: 4px 8px;
            font-size: 12px;
        }

        .loading-patients, .no-agendas {
            text-align: center;
            padding: 20px;
            color: #666;
            font-style: italic;
        }

        .token-display {
            display: flex;
            gap: 8px;
            align-items: center;
            margin-top: 5px;
        }

        .token-display input {
            flex: 1;
            font-family: monospace;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 6px 10px;
            border-radius: 4px;
        }

        .info-item {
            margin-bottom: 15px;
        }

        .slot-summary {
            background: #f8f9fa;
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 8px;
            border-left: 3px solid #007bff;
        }

        .slot-summary.occupied {
            border-left-color: #28a745;
            background: #f8fff9;
        }
        </style>
        `;
    }

    /**
     * Inicializar eventos después de renderizar
     */
    async initEvents() {
        // Cargar datos guardados
        this.loadLocalData();
        
        // Controles de pacientes
        document.getElementById('refreshPatientsBtn').addEventListener('click', () => {
            this.loadPatientsFromServer();
        });

        document.getElementById('uploadPatientBtn').addEventListener('click', () => {
            this.uploadCurrentPatient();
        });

        document.getElementById('importJsonBtn').addEventListener('click', () => {
            document.getElementById('importJsonFile').click();
        });

        document.getElementById('importJsonFile').addEventListener('change', (e) => {
            this.importJsonFile(e.target.files[0]);
        });

        // Controles de agendas
        document.getElementById('createAgendaBtn').addEventListener('click', () => {
            this.openAgendaModal();
        });

        document.getElementById('duplicateAgendaBtn').addEventListener('click', () => {
            this.duplicateAgenda();
        });

        // Modal de agenda
        document.getElementById('cancelAgendaBtn').addEventListener('click', () => {
            this.closeAgendaModal();
        });

        document.getElementById('saveAgendaBtn').addEventListener('click', () => {
            this.saveAgenda();
        });

        document.getElementById('addSlotBtn').addEventListener('click', () => {
            this.addTimeSlot();
        });

        // Modal de detalles
        document.getElementById('editAgendaBtn').addEventListener('click', () => {
            this.editCurrentAgenda();
        });

        document.getElementById('deleteAgendaBtn').addEventListener('click', () => {
            this.deleteCurrentAgenda();
        });

        document.getElementById('closeDetailsBtn').addEventListener('click', () => {
            this.closeDetailsModal();
        });

        document.getElementById('copyTokenBtn').addEventListener('click', () => {
            this.copyAgendaToken();
        });

        // Cargar datos iniciales
        this.loadPatientsFromServer();
        this.renderAgendas();
        this.checkCurrentPatient();
    }

    /**
     * Cargar pacientes desde el servidor
     */
    async loadPatientsFromServer() {
        try {
            const response = await fetch('https://tmeduca.org/labsim/php/patients-api.php?action=list');
            if (response.ok) {
                this.patients = await response.json();
                this.renderPatients();
            } else {
                this.app.notify('Error cargando pacientes del servidor', 'warning');
                this.patients = [];
                this.renderPatients();
            }
        } catch (error) {
            this.app.notify('No se pudo conectar con el servidor', 'warning');
            this.patients = [];
            this.renderPatients();
        }
    }

    /**
     * Renderizar lista de pacientes
     */
    renderPatients() {
        const container = document.getElementById('patientsList');
        
        if (this.patients.length === 0) {
            container.innerHTML = '<div class="loading-patients">No hay pacientes guardados</div>';
            return;
        }

        container.innerHTML = this.patients.map(patient => `
            <div class="patient-item" data-patient-id="${patient.id}">
                <div class="patient-name">${patient.name}</div>
                <div class="patient-info">
                    <span>👤 ${patient.age || 'N/A'} años</span>
                    <span>📅 ${patient.created || 'Sin fecha'}</span>
                    <span>🏥 ${patient.diagnosis || 'Sin diagnóstico'}</span>
                </div>
            </div>
        `).join('');

        // Agregar event listeners
        container.querySelectorAll('.patient-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectPatient(item.dataset.patientId);
            });
        });
    }

    /**
     * Seleccionar paciente
     */
    selectPatient(patientId) {
        // Actualizar selección visual
        document.querySelectorAll('.patient-item').forEach(item => {
            item.classList.remove('selected');
        });
        document.querySelector(`[data-patient-id="${patientId}"]`).classList.add('selected');

        // Cargar datos del paciente
        this.selectedPatient = this.patients.find(p => p.id === patientId);
        
        if (this.selectedPatient) {
            this.loadPatientData(this.selectedPatient);
            this.app.notify(`Paciente "${this.selectedPatient.name}" cargado`, 'success');
        }
    }

    /**
     * Cargar datos del paciente en la aplicación
     */
    async loadPatientData(patient) {
        try {
            // Cargar JSON completo del paciente
            const response = await fetch(`https://tmeduca.org/labsim/php/patients-api.php?action=get&id=${patient.id}`);
            if (response.ok) {
                const patientData = await response.json();
                this.app.importJSON(patientData);
                
                // Ir al primer módulo de datos
                await this.app.tabManager.goToTab(1); // Asumiendo que agenda es índice 0
            } else {
                this.app.notify('Error cargando datos del paciente', 'error');
            }
        } catch (error) {
            this.app.notify('Error cargando datos del paciente', 'error');
        }
    }

    /**
     * Subir paciente actual al servidor
     */
    async uploadCurrentPatient() {
        if (!this.hasCurrentPatientData()) {
            this.app.notify('No hay datos de paciente para subir', 'warning');
            return;
        }

        try {
            const patientData = this.app.exportJSON();
            const formData = new FormData();
            formData.append('action', 'upload');
            formData.append('password', this.apiPassword);
            formData.append('data', patientData);

            const response = await fetch('https://tmeduca.org/labsim/php/patients-api.php', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.app.notify('Paciente subido correctamente', 'success');
                this.loadPatientsFromServer(); // Actualizar lista
            } else {
                this.app.notify('Error subiendo paciente', 'error');
            }
        } catch (error) {
            this.app.notify('Error conectando con el servidor', 'error');
        }
    }

    /**
     * Importar archivo JSON
     */
    importJsonFile(file) {
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const jsonData = JSON.parse(e.target.result);
                this.app.importJSON(jsonData);
                this.app.notify('Archivo JSON importado correctamente', 'success');
                this.checkCurrentPatient();
            } catch (error) {
                this.app.notify('Error leyendo archivo JSON', 'error');
            }
        };
        reader.readAsText(file);
    }

    /**
     * Verificar si hay datos de paciente actual
     */
    hasCurrentPatientData() {
        return this.app.currentData && Object.keys(this.app.currentData).length > 0;
    }

    /**
     * Verificar paciente actual y habilitar botones
     */
    checkCurrentPatient() {
        const uploadBtn = document.getElementById('uploadPatientBtn');
        if (uploadBtn) {
            uploadBtn.disabled = !this.hasCurrentPatientData();
        }
    }

    /**
     * Abrir modal de agenda
     */
    openAgendaModal(agenda = null) {
        this.currentAgenda = agenda;
        const modal = document.getElementById('agendaModal');
        
        if (agenda) {
            // Modo edición
            document.getElementById('agendaName').value = agenda.name;
            document.getElementById('agendaDescription').value = agenda.description || '';
            this.renderAgendaSlots(agenda.slots || []);
        } else {
            // Modo creación
            document.getElementById('agendaName').value = '';
            document.getElementById('agendaDescription').value = '';
            this.renderAgendaSlots([]);
            this.addTimeSlot(); // Agregar un slot inicial
        }
        
        modal.style.display = 'flex';
    }

    /**
     * Cerrar modal de agenda
     */
    closeAgendaModal() {
        document.getElementById('agendaModal').style.display = 'none';
        this.currentAgenda = null;
    }

    /**
     * Renderizar slots de horarios en el modal
     */
    renderAgendaSlots(slots) {
        const container = document.getElementById('slotsContainer');
        container.innerHTML = '';

        slots.forEach((slot, index) => {
            this.addTimeSlot(slot, index);
        });
    }

    /**
     * Agregar slot de tiempo
     */
    addTimeSlot(slotData = null, index = null) {
        const container = document.getElementById('slotsContainer');
        const slotIndex = index !== null ? index : container.children.length;
        
        const slotDiv = document.createElement('div');
        slotDiv.className = 'slot-item';
        slotDiv.innerHTML = `
            <input type="date" class="slot-input date" value="${slotData?.date || ''}" placeholder="Fecha">
            <input type="time" class="slot-input time" value="${slotData?.time || ''}" placeholder="Hora">
            <input type="number" class="slot-input duration" value="${slotData?.duration || 30}" 
                   placeholder="Min" min="15" max="180" step="15">
            <select class="slot-patient-select">
                <option value="">-- Sin asignar --</option>
                ${this.patients.map(p => `
                    <option value="${p.id}" ${slotData?.patientId === p.id ? 'selected' : ''}>
                        ${p.name}
                    </option>
                `).join('')}
            </select>
            <button type="button" class="btn btn-danger btn-sm" onclick="this.parentElement.remove()">🗑️</button>
        `;
        
        container.appendChild(slotDiv);
    }

    /**
     * Guardar agenda
     */
    saveAgenda() {
        const name = document.getElementById('agendaName').value.trim();
        if (!name) {
            this.app.notify('El nombre de la agenda es requerido', 'warning');
            return;
        }

        const description = document.getElementById('agendaDescription').value.trim();
        const slots = this.collectSlotsData();

        const agenda = {
            id: this.currentAgenda?.id || this.generateId(),
            name: name,
            description: description,
            slots: slots,
            token: this.currentAgenda?.token || this.generateToken(),
            created: this.currentAgenda?.created || new Date().toISOString(),
            updated: new Date().toISOString()
        };

        if (this.currentAgenda) {
            // Actualizar agenda existente
            const index = this.agendas.findIndex(a => a.id === this.currentAgenda.id);
            if (index !== -1) {
                this.agendas[index] = agenda;
            }
        } else {
            // Nueva agenda
            this.agendas.push(agenda);
        }

        this.saveLocalData();
        this.renderAgendas();
        this.closeAgendaModal();
        
        this.app.notify(`Agenda "${name}" guardada correctamente`, 'success');
    }

    /**
     * Recopilar datos de slots
     */
    collectSlotsData() {
        const slots = [];
        const slotItems = document.querySelectorAll('.slot-item');
        
        slotItems.forEach(item => {
            const date = item.querySelector('.date').value;
            const time = item.querySelector('.time').value;
            const duration = parseInt(item.querySelector('.duration').value) || 30;
            const patientId = item.querySelector('.slot-patient-select').value;
            
            if (date && time) {
                slots.push({
                    date: date,
                    time: time,
                    duration: duration,
                    patientId: patientId || null,
                    patientName: patientId ? this.patients.find(p => p.id === patientId)?.name : null
                });
            }
        });
        
        return slots.sort((a, b) => {
            const dateTimeA = new Date(`${a.date}T${a.time}`);
            const dateTimeB = new Date(`${b.date}T${b.time}`);
            return dateTimeA - dateTimeB;
        });
    }

    /**
     * Renderizar lista de agendas
     */
    renderAgendas() {
        const container = document.getElementById('agendasList');
        
        if (this.agendas.length === 0) {
            container.innerHTML = '<div class="no-agendas">No hay agendas creadas</div>';
            document.getElementById('duplicateAgendaBtn').disabled = true;
            return;
        }

        container.innerHTML = this.agendas.map(agenda => `
            <div class="agenda-item" data-agenda-id="${agenda.id}">
                <div class="agenda-name">${agenda.name}</div>
                <div class="agenda-info">
                    <div>📅 ${agenda.slots.length} horarios</div>
                    <div>🔑 <span class="agenda-token">${agenda.token}</span></div>
                </div>
            </div>
        `).join('');

        // Agregar event listeners
        container.querySelectorAll('.agenda-item').forEach(item => {
            item.addEventListener('click', () => {
                this.showAgendaDetails(item.dataset.agendaId);
            });
        });

        document.getElementById('duplicateAgendaBtn').disabled = false;
    }

    /**
     * Mostrar detalles de agenda
     */
    showAgendaDetails(agendaId) {
        const agenda = this.agendas.find(a => a.id === agendaId);
        if (!agenda) return;

        this.currentAgenda = agenda;
        
        document.getElementById('agendaDetailsTitle').textContent = `📅 ${agenda.name}`;
        document.getElementById('agendaToken').value = agenda.token;
        
        const content = document.getElementById('agendaDetailsContent');
        content.innerHTML = `
            <div class="info-item">
                <strong>Descripción:</strong>
                <p>${agenda.description || 'Sin descripción'}</p>
            </div>
            
            <div class="info-item">
                <strong>Horarios de Atención:</strong>
                <div style="margin-top: 10px;">
                    ${agenda.slots.map(slot => `
                        <div class="slot-summary ${slot.patientId ? 'occupied' : ''}">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>${this.formatDate(slot.date)} - ${slot.time}</strong>
                                    <span style="color: #666; margin-left: 10px;">(${slot.duration} min)</span>
                                </div>
                                <div>
                                    ${slot.patientId ? 
                                        `👤 ${slot.patientName}` : 
                                        '<span style="color: #999;">Disponible</span>'
                                    }
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="info-item">
                <strong>Estadísticas:</strong>
                <ul style="margin-top: 5px; margin-left: 20px;">
                    <li>Total de horarios: ${agenda.slots.length}</li>
                    <li>Ocupados: ${agenda.slots.filter(s => s.patientId).length}</li>
                    <li>Disponibles: ${agenda.slots.filter(s => !s.patientId).length}</li>
                </ul>
            </div>
        `;
        
        document.getElementById('agendaDetailsModal').style.display = 'flex';
    }

    /**
     * Cerrar modal de detalles
     */
    closeDetailsModal() {
        document.getElementById('agendaDetailsModal').style.display = 'none';
        this.currentAgenda = null;
    }

    /**
     * Editar agenda actual
     */
    editCurrentAgenda() {
        if (this.currentAgenda) {
            this.closeDetailsModal();
            this.openAgendaModal(this.currentAgenda);
        }
    }

    /**
     * Eliminar agenda actual
     */
    deleteCurrentAgenda() {
        if (!this.currentAgenda) return;
        
        if (confirm(`¿Estás seguro de eliminar la agenda "${this.currentAgenda.name}"?`)) {
            this.agendas = this.agendas.filter(a => a.id !== this.currentAgenda.id);
            this.saveLocalData();
            this.renderAgendas();
            this.closeDetailsModal();
            this.app.notify('Agenda eliminada', 'info');
        }
    }

    /**
     * Duplicar agenda seleccionada
     */
    duplicateAgenda() {
        // Obtener agenda seleccionada (la primera por ahora)
        if (this.agendas.length === 0) return;
        
        const sourceAgenda = this.agendas[0]; // Por simplicidad, duplicar la primera
        const newAgenda = {
            ...sourceAgenda,
            id: this.generateId(),
            name: `${sourceAgenda.name} (Copia)`,
            token: this.generateToken(),
            created: new Date().toISOString(),
            updated: new Date().toISOString(),
            slots: sourceAgenda.slots.map(slot => ({
                ...slot,
                patientId: null, // Limpiar asignaciones
                patientName: null
            }))
        };
        
        this.agendas.push(newAgenda);
        this.saveLocalData();
        this.renderAgendas();
        this.app.notify('Agenda duplicada correctamente', 'success');
    }

    /**
     * Copiar token de agenda
     */
    copyAgendaToken() {
        const tokenInput = document.getElementById('agendaToken');
        tokenInput.select();
        document.execCommand('copy');
        this.app.notify('Token copiado al portapapeles', 'success');
    }

    /**
     * Formatear fecha para mostrar
     */
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('es-ES', { 
            weekday: 'short', 
            day: 'numeric', 
            month: 'short' 
        });
    }

    /**
     * Generar ID único
     */
    generateId() {
        return 'agenda_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Generar token aleatorio
     */
    generateToken() {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        let token = '';
        for (let i = 0; i < 8; i++) {
            token += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return token;
    }

    /**
     * Guardar datos localmente
     */
    saveLocalData() {
        try {
            localStorage.setItem('labsim_agendas', JSON.stringify(this.agendas));
            localStorage.setItem('labsim_agenda_timestamp', Date.now().toString());
        } catch (error) {
            this.app.handleError('Error guardando agendas', error);
        }
    }

    /**
     * Cargar datos locales
     */
    loadLocalData() {
        try {
            const savedAgendas = localStorage.getItem('labsim_agendas');
            if (savedAgendas) {
                this.agendas = JSON.parse(savedAgendas);
            }
        } catch (error) {
            this.app.handleError('Error cargando agendas guardadas', error);
            this.agendas = [];
        }
    }

    /**
     * Obtener datos del módulo
     */
    getData() {
        return {
            selected_patient: this.selectedPatient?.id || null,
            current_agenda: this.currentAgenda?.id || null,
            agendas_count: this.agendas.length,
            patients_count: this.patients.length,
            last_sync: new Date().toISOString()
        };
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        // La agenda no requiere validación específica
        return {
            isValid: true,
            errors: []
        };
    }

    /**
     * Verificar si está completo
     */
    isComplete(data) {
        // La agenda siempre se considera completa
        return true;
    }

    /**
     * Limpiar selecciones
     */
    clearSelections() {
        this.selectedPatient = null;
        this.currentAgenda = null;
        
        // Limpiar selecciones visuales
        document.querySelectorAll('.patient-item.selected').forEach(item => {
            item.classList.remove('selected');
        });
        
        document.querySelectorAll('.agenda-item.selected').forEach(item => {
            item.classList.remove('selected');
        });
    }
}

// Exponer globalmente
window.AgendaModule = AgendaModule;
