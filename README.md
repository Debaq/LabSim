# LabSim

Simulador de laboratorio de audiología y otoneurología para formación clínica.
Reemplaza el equipamiento físico (audiómetro, ABR, impedanciometría, etc.) por
una plataforma de software que reproduce fielmente su comportamiento, permitiendo
a estudiantes practicar exámenes y protocolos sin necesidad de hardware real.

## Módulos

- **Audiómetro** (`Audiometer.py`): umbrales tonales, logoaudiometría, Fowler,
  Stenger, SISI y decaimiento tonal. Estímulos generados por síntesis (tonos y
  ruidos), no archivos de audio estáticos.
- **ABR** (`ABR.py`, `abr_module.py`): potenciales evocados auditivos de tronco.
- **Agenda** (`Agenda.py`): gestión de casos y pacientes simulados, con flujo
  tipo ficha clínica.
- **CVC / Z-meter / MKG**: pruebas complementarias de otoneurología.
- **ListWords**: gestión de listas de palabras para logoaudiometría.

El programa además soporta un **teclado físico dedicado** (firmware en
`firmware/labsim_keyboard`) para controlar diales y botones del audiómetro
como en un equipo real.

## Requisitos

- Python 3.10
- PySide6
- pyqtgraph
- numpy, requests, cryptocode, bezier, pyudev

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecutar

```bash
python src/main.py
```

## Compilar (build)

El proyecto se empaqueta con PyInstaller (`LabSim.spec`):

```bash
./build.sh
```

Este script activa el entorno `micromamba` llamado `labsim` y ejecuta PyInstaller
para generar el ejecutable en `dist/`.

## Estructura

```
src/            Código fuente de la aplicación
resources/      Configuración, assets, audio, plantillas, estilos y JSON de datos
firmware/       Firmware del teclado físico LabSim
labsim-backend/ Backend asociado al proyecto
icons/          Íconos de la aplicación
```

## Licencia

MIT © Nicolás Quezada Baier
