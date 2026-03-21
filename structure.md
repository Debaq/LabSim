LabSim3/
├── main.py                      # Entry point único - inicializa la aplicación
├── requirements.txt             # Dependencias Python del proyecto
├── pyproject.toml              # Configuración del proyecto y build
├── README.md                   # Documentación principal del proyecto
├── .gitignore                  # Archivos a ignorar en git
│
├── src/                        # Código fuente principal
│   ├── __init__.py            # Marca el directorio como package Python
│   │
│   ├── config/                 # Configuración centralizada del sistema
│   │   ├── __init__.py        # Exporta configuraciones principales
│   │   ├── settings.py        # Settings globales (rutas, defaults, etc.)
│   │   └── constants.py       # Constantes audiológicas (frecuencias, límites)
│   │
│   ├── core/                   # Núcleo del sistema (lógica sin GUI)
│   │   ├── __init__.py        # Exporta clases principales del core
│   │   ├── hardware_detector.py # Detecta capacidades GPU/CPU/RAM/Red
│   │   ├── ai_strategy.py     # Selecciona estrategia IA óptima
│   │   └── audio_engine.py    # Motor de generación de audio procedural
│   │
│   ├── models/                 # Modelos de datos y estructuras
│   │   ├── __init__.py        # Exporta todos los modelos
│   │   ├── case.py            # Modelo de caso clínico (JSON schema)
│   │   ├── session.py         # Modelos de sesión audiológica
│   │   └── audiometry.py      # Modelos de datos audiométricos/impedancia/OAE/ABR
│   │
│   ├── simulation/             # Sistema de simulación del paciente
│   │   ├── __init__.py        # Exporta componentes de simulación
│   │   ├── patient_simulator.py # Gestor principal de simulación del paciente
│   │   ├── case_interpreter.py # Interpreta datos del caso JSON
│   │   └── response_generator.py # Genera respuestas basadas en el caso
│   │
│   ├── ai/                     # Sistema de inteligencia artificial
│   │   ├── __init__.py        # Exporta componentes de IA
│   │   ├── speech_to_text.py  # STT local (Whisper) y APIs cloud
│   │   ├── text_to_speech.py  # TTS local (Piper) y APIs cloud
│   │   └── conversation_manager.py # Gestiona conversaciones con paciente
│   │
│   ├── gui/                    # Interfaz gráfica de usuario completa
│   │   ├── __init__.py        # Exporta componentes GUI principales
│   │   ├── application.py     # QApplication y configuración GUI
│   │   ├── main_window.py     # Ventana principal MDI fullscreen con toolbar
│   │   │
│   │   ├── modules/           # Módulos audiológicos (ventanas sobre MDI)
│   │   │   ├── __init__.py    # Exporta todos los módulos
│   │   │   ├── audiometer_window.py # Ventana audiometría sobre MDI
│   │   │   ├── impedance_window.py  # Ventana impedancia sobre MDI
│   │   │   ├── oae_window.py        # Ventana OAE sobre MDI
│   │   │   └── abr_window.py        # Ventana ABR sobre MDI
│   │   │
│   │   ├── widgets/           # Widgets comunes reutilizables
│   │   │   ├── __init__.py    # Exporta todos los widgets
│   │   │   ├── patient_chat.py # Widget de chat con paciente IA
│   │   │   ├── patient_info.py # Widget información del caso actual
│   │   │   ├── audiogram_display.py # Display de audiograma
│   │   │   └── tympanogram_display.py # Display de timpanograma
│   │   │
│   │   └── dialogs/           # Diálogos y ventanas secundarias
│   │       ├── __init__.py    # Exporta todos los diálogos
│   │       ├── case_selector.py # Selector de casos clínicos
│   │       ├── settings_dialog.py # Configuración de usuario
│   │       └── case_editor.py # Editor de casos clínicos
│   │
│   ├── hardware/               # Soporte de hardware físico
│   │   ├── __init__.py        # Exporta drivers de hardware
│   │   ├── console_driver.py  # Driver para consola física personalizada
│   │   └── audio_interface.py # Interfaz de audio (ASIO/DirectSound)
│   │
│   ├── database/               # Gestión de base de datos
│   │   ├── __init__.py        # Exporta gestores de BD
│   │   ├── sqlite_manager.py  # Gestor SQLite local para sesiones
│   │   ├── case_manager.py    # Gestor de casos JSON
│   │   └── sync_manager.py    # Sincronización con servidor web
│   │
│   ├── api/                    # Cliente para APIs externas
│   │   ├── __init__.py        # Exporta clientes API
│   │   ├── client.py          # Cliente API REST del servidor web
│   │   └── moodle_integration.py # Integración LTI con Moodle
│   │
│   └── utils/                  # Utilidades y helpers generales
│       ├── __init__.py        # Exporta utilidades comunes
│       ├── helpers.py         # Funciones helper generales
│       ├── logging_config.py  # Configuración de logging
│       └── exceptions.py      # Excepciones customizadas del sistema
│
├── resources/                  # Recursos estáticos del proyecto
│   ├── config/                # Archivos de configuración
│   │   ├── default_config.json # Configuración por defecto
│   │   └── ai_strategies.json # Estrategias de IA disponibles
│   │
│   ├── cases/                 # Casos clínicos en JSON
│   │   ├── case_001.json      # Caso básico: pérdida conductiva leve
│   │   ├── case_002.json      # Caso intermedio: presbiacusia
│   │   ├── case_003.json      # Caso avanzado: hipoacusia neurosensorial
│   │   └── case_template.json # Template para crear casos nuevos
│   │
│   └── ui/                    # Recursos de interfaz de usuario
│       ├── styles/            # Archivos de estilo Qt
│       │   └── main.qss       # Stylesheet principal
│       ├── icons/             # Iconos de la aplicación y módulos
│       │   ├── audiometer.png # Icono módulo audiometría
│       │   ├── impedance.png  # Icono módulo impedancia
│       │   ├── oae.png        # Icono módulo OAE
│       │   ├── abr.png        # Icono módulo ABR
│       │   └── cases.png      # Icono selector de casos
│       └── layouts/           # Layouts XML/UI pre-diseñados
│
├── scripts/                   # Scripts de construcción y deployment
│   ├── build_nuitka.py        # Script de build con Nuitka
│   ├── build_pyinstaller.py   # Script de build con PyInstaller
│   └── setup_dev.py           # Configuración entorno desarrollo
│
├── build/                     # Archivos temporales de build (gitignored)
├── dist/                      # Ejecutables finales (gitignored)
└── logs/                      # Logs de aplicación
    └── .gitkeep              # Mantiene directorio en git
