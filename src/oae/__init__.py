"""OEA (Otoemisiones Acústicas) - módulo clínico.

Emisor otoacústico clínico para LabSim. Cuatro pruebas en una sola ventana
con tabs: TEOAE (transientes), DPOAE (producto de distorsión), SOAE
(espontáneas, sin estímulo) y SFOAE (frecuencia de estímulo / supresión).
Síntesis 100% sintética (sin hardware), mismos patrones que ABR (QMainWindow,
pyqtgraph GraphicsLayoutWidget, QTimer para captura, normativos via
core.app_config_store).
"""
