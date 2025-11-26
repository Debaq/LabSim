# LabSim 3.0 - Generador de Perfil de Paciente Audiológico

## 📋 Estado Actual del Proyecto

### ✅ COMPLETADO - Core Básico (100%)

El sistema base está **completamente funcional** con arquitectura modular escalable.

#### **Archivos Implementados:**
```
audiogram-form-generator/
├── index.html ✅ (Estructura base limpia)
├── css/
│   ├── main.css ✅ (Estilos base profesionales)
│   └── form-components.css ✅ (Componentes reutilizables)
└── js/core/
    ├── app.js ✅ (Aplicación principal)
    ├── tab-manager.js ✅ (Gestor de navegación)
    └── notification-manager.js ✅ (Sistema de notificaciones)
```

#### **Funcionalidades Operativas:**
- ✅ **Sistema de tabs dinámico** con 10 módulos configurados
- ✅ **Carga dinámica** de componentes JavaScript
- ✅ **Navegación fluida** con animaciones y estados visuales
- ✅ **Auto-guardado** cada 30 segundos en localStorage
- ✅ **Sistema de notificaciones** con 4 tipos y auto-remove
- ✅ **Validación en tiempo real** y gestión de datos
- ✅ **Prevención de pérdida** de datos al cerrar
- ✅ **Navegación con teclado** (Ctrl + flechas)
- ✅ **Responsive design** completo

---

## 🏗️ Arquitectura del Sistema

### **Patrón de Diseño:**
- **Modular**: Cada ficha es un componente independiente
- **Lazy Loading**: Módulos se cargan solo cuando se necesitan
- **Event-Driven**: Comunicación por eventos entre componentes
- **Data-Centric**: Estado centralizado en `app.currentData`

### **Flujo de Funcionamiento:**
```
1. app.js inicializa el sistema
2. tab-manager.js maneja navegación
3. Módulos se cargan dinámicamente desde js/components/
4. Datos se almacenan en app.currentData[moduleId]
5. JSON final se genera combinando todos los datos
```

### **Convenciones de Código:**
- **Clases**: PascalCase (ej: `PatientInfoModule`)
- **Archivos**: kebab-case (ej: `patient-info.js`)
- **IDs de módulos**: kebab-case (ej: `patient-info`)
- **Métodos**: camelCase (ej: `updateModuleData`)

---

## 📁 Módulos Configurados (Pendientes de Implementar)

### **REQUERIDOS (obligatorios para export):**
1. **`patient-info`** 👤 - Información Básica
2. **`anamnesis`** 📋 - Historia clínica
3. **`audiometry`** 🎧 - Umbrales auditivos (125-20K Hz)
4. **`json-output`** 📄 - Resultado final

### **OPCIONALES (mejoran el perfil):**
5. **`logoaudiometry`** 🗣️ - SDT, SRT, discriminación
6. **`supraliminal`** 📊 - Reclutamiento y deterioro
7. **`impedance`** 📈 - Timpanograma y reflejos ⭐
8. **`oae`** 🌊 - Emisiones otoacústicas
9. **`abr`** ⚡ - Potenciales evocados ⭐
10. **`electrocochleo`** 🔬 - Electrocoleografía

⭐ = **Incluyen preview visual en tiempo real**

---

## 🎯 Estructura JSON Objetivo

### **Esquema Completo de Datos:**
```json
{
  "metadata": {
    "schema_version": "1.0",
    "created_date": "2024-XX-XX",
    "generator_version": "3.0.0"
  },
  "patient_info": {
    "nombre": "string",
    "edad": "number",
    "genero": "M/F"
  },
  "perfil_ia_paciente": {
    "personalidad": {
      "cooperacion": 0.8,
      "ansiedad": 0.6
    },
    "patrones_respuesta": {
      "tiempo_respuesta_ms": 800,
      "falsos_positivos": 0.15
    }
  },
  "anamnesis": {
    "motivo_consulta": {},
    "historia_libre": {},
    "antecedentes_morbidos": {},
    "exposicion_ruido": {},
    "tinnitus": {}
  },
  "audiometria": {
    "umbrales_aereos": {
      "oido_derecho": {
        "125": null, "250": 25, "500": 30,
        "1000": 40, "2000": 50, "4000": 65,
        "8000": 75, "10000": null, "12500": null,
        "16000": null, "20000": null
      }
    },
    "umbrales_oseos": {},
    "ldl_disconfort": {}
  },
  "logoaudiometria": {
    "sdt_deteccion": {},
    "srt_audibilidad": {},
    "umd_inteligibilidad": {}
  },
  "pruebas_deterioro": {
    "stat": {}, "carhart": {}, "maspetiol": {}
  },
  "pruebas_reclutamiento": {
    "fowler_ablb": {}, "sisi": {}, "luscher_zwislocki": {}
  },
  "impedanciometria": {
    "timpanometria": {},
    "reflejos_acusticos": {}
  },
  "eoa": {
    "transientes_clinicas": {},
    "producto_distorsion_clinicas": {}
  },
  "abr": {
    "click": {}, "tone_burst": {}, "chirp": {}
  },
  "electrocoleografia": {
    "potencial_sumacion": -0.25,
    "potencial_accion": 2.85
  }
}
```

---

## 🔧 Guía para Implementar Módulos

### **Template Base para Módulos:**
```javascript
/**
 * ModuloModule - Descripción del módulo
 */
class ModuloModule {
    constructor(app) {
        this.app = app;
        this.moduleId = 'modulo-id';
    }

    /**
     * Renderizar contenido del módulo
     */
    async render(existingData = {}) {
        return `
            <div class="form-section">
                <h3 class="section-title">Título del Módulo</h3>
                <!-- Contenido HTML aquí -->
            </div>
        `;
    }

    /**
     * Inicializar eventos después de renderizar
     */
    initEvents() {
        // Event listeners aquí
    }

    /**
     * Obtener datos del formulario
     */
    getData() {
        return {
            // Datos extraídos del DOM
        };
    }

    /**
     * Validar datos del módulo
     */
    validate(data) {
        return {
            isValid: true,
            errors: []
        };
    }

    /**
     * Verificar si está completo
     */
    isComplete(data) {
        return data && Object.keys(data).length > 0;
    }
}
```

### **Pasos para Agregar un Módulo:**
1. **Crear archivo** en `js/components/nombre-modulo.js`
2. **Implementar clase** siguiendo el template
3. **El sistema cargará automáticamente** el módulo cuando sea necesario
4. **No modificar** app.js ni tab-manager.js

---

## 🎨 Previews Visuales Pendientes

### **1. Audiograma (PRIORIDAD ALTA)**
- **Frecuencias**: 125 Hz a 20.000 Hz
- **Toggle alta frecuencia**: Mostrar/ocultar 9K-20K
- **Símbolos estándar**:
  - OD Aéreo: ○——○ (círculos rojos, línea continua)
  - OI Aéreo: ×——× (X azules, línea continua)
  - OD Óseo: <⋯⋯< (símbolos rojos, línea punteada)
  - OI Óseo: >⋯⋯> (símbolos azules, línea punteada)
- **Grilla profesional** con línea gruesa en 20 dB
- **Actualización en tiempo real** al cambiar umbrales

### **2. Timpanograma (MEDIANA)**
- **Gráfico compliance vs presión** (-400 a +200 daPa)
- **Tipos de curva**:
  - Tipo A: Pico normal en ~0 daPa
  - Tipo B: Curva plana (sin pico)
  - Tipo C: Pico desplazado (-150 a -300 daPa)
- **Tabla de reflejos** con indicadores de color
- **Canvas 2D** suficiente para implementar

### **3. ABR (COMPLEJO)**
- **Ondas I, III, V simuladas** con latencias correctas
- **Morfología realista** de ondas bifásicas
- **Curvas latencia-intensidad** por onda
- **Múltiples estímulos** (click, burst, chirp)
- **Requiere matemáticas complejas** para formas de onda

---

## 🚨 Puntos Críticos a Recordar

### **Convenciones Audiológicas:**
- **Frecuencias arriba** del audiograma (no abajo)
- **Línea más gruesa en 20 dB** (límite normalidad)
- **Vía ósea posicionada lateralmente** (< a la izq, > a la der)
- **Líneas punteadas** para vía ósea
- **80 dB como referencia** principal en ABR

### **Funcionalidades Especiales:**
- **Auto-guardado** cada 30 segundos
- **Validación en tiempo real** opcional por módulo
- **Navegación con teclado** (Ctrl + flechas)
- **Notificaciones** para feedback del usuario
- **Exportación JSON** cuando módulos requeridos estén completos

### **Patrones de Datos:**
- **null** para umbrales no obtenidos
- **Escalas específicas**: 0-1 para personalidad, % para SISI
- **Convenciones de naming**: camelCase para propiedades

---

## 🔄 Siguiente Sesión - Plan de Acción

### **OPCIÓN A - Módulo Simple (Recomendado)**
**Implementar `patient-info.js`**:
- Datos demográficos básicos
- Perfil de personalidad IA
- Diagnóstico patológico
- **Ventaja**: Simple, permite probar el sistema

### **OPCIÓN B - Módulo con Preview**
**Implementar `audiometry.js`**:
- Umbrales 125-20.000 Hz
- Toggle alta frecuencia
- Preview audiograma en tiempo real
- **Ventaja**: Funcionalidad visual impresionante

### **OPCIÓN C - Módulo Especializado**
**Implementar `impedance.js`**:
- Timpanograma con tipos A/B/C
- Reflejos acústicos
- Preview visual del timpanograma
- **Ventaja**: Demuestra capacidades avanzadas

### **Comando para Continuar:**
```
"Continúa implementando [módulo elegido] para LabSim 3.0.
Ya tengo el core básico funcionando según la documentación."
```

---

## 📚 Recursos Técnicos

### **Canvas para Previews:**
- **Context 2D** para audiograma e impedancia
- **Animaciones** con requestAnimationFrame
- **Responsive** con devicePixelRatio
- **Exportación** a PNG/PDF opcional

### **Validaciones:**
- **Umbrales**: 0-120 dB HL
- **Frecuencias**: 125-20.000 Hz
- **Personalidad**: Escalas 0-1
- **Consistencia**: Gaps aéreo-óseo válidos

### **Persistencia:**
- **Auto-save**: localStorage cada 30s
- **Exportación**: JSON con timestamp
- **Importación**: Cargar perfil existente
- **Templates**: Casos predefinidos por patología

### **Estructura de directorios actual:**
```
web/
├── .htaccess
├── index.html
├── project_documentation.md
├── css/
│   ├── modules/
│   ├── form-components.css
│   └── main.css
├── js/
│   ├── components/ (pendientes por implementar)
│   └── core/
│       ├── app.js
│       ├── tab-manager.js
│       └── notification-manager.js
├── php/ (por implementar)
└── templates/ (por implementar)
```

---

## 🎯 Objetivo Final

Un **generador completo de perfiles de pacientes audiológicos** que produzca JSONs listos para usar en LabSim 3.0, con:

- ✅ **Interfaz profesional** tipo software médico
- ✅ **Previews visuales** de audiograma y timpanograma
- ✅ **Validación clínica** de datos consistentes
- ✅ **Exportación perfecta** para simulación de pacientes IA
- ✅ **Escalabilidad** para agregar nuevas pruebas audiológicas

**El sistema está listo para continuar implementando módulos individualmente.**

## 📝 Progreso Actual de Desarrollo

### Estado de los componentes:
- js/core/app.js ✅ (Completado)
- js/core/tab-manager.js ✅ (Completado)
- js/core/notification-manager.js ✅ (Completado)
- js/components/ 📁 (Vacío - pendientes de implementar)
- css/modules/ 📁 (Vacío - posiblemente por implementar)

### Próximos pasos recomendados:
1. Implementar el módulo `patient-info.js` como primer componente funcional
2. Crear la estructura visual y lógica para el módulo de información básica del paciente
3. Probar la integración con el sistema de auto-guardado y validación
4. Implementar módulos adicionales según prioridad clínica