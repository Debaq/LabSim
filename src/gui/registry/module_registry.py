"""
module_registry.py - Registry de módulos para gestionar ventanas
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Sistema de registry que permite abrir módulos sin hard-coding en main_window.
Por ahora solo soporta TextPro, preparado para futuros módulos audiológicos.
"""

from typing import Optional, Dict, Callable, Any


class ModuleRegistry:
    """Registry para gestionar la creación de módulos."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self._modules: Dict[str, Callable] = {}
        self._register_modules()
    
    def _register_modules(self):
        """Registra todos los módulos disponibles."""
        # Por ahora solo TextPro está implementado
        self._modules["TextPro"] = self._create_textpro
        
        # Módulos futuros (placeholder para preparar la estructura)
        self._modules["Audiometría"] = self._module_not_implemented
        self._modules["Impedancia"] = self._module_not_implemented
        self._modules["OAE"] = self._module_not_implemented
        self._modules["ABR"] = self._module_not_implemented
        self._modules["Casos"] = self._module_not_implemented
        self._modules["Config"] = self._module_not_implemented
    
    def create_module(self, module_name: str) -> Optional[Any]:
        """Crea una instancia del módulo especificado."""
        if module_name in self._modules:
            return self._modules[module_name]()
        else:
            print(f"Módulo '{module_name}' no encontrado en el registry")
            return None
    
    def _create_textpro(self):
        """Crea una instancia de TextPro."""
        # Import local para evitar dependencias circulares
        from ..dialogs.textpro_window import TextProWindow
        return TextProWindow(self.main_window)
    
    def _module_not_implemented(self):
        """Placeholder para módulos no implementados aún."""
        print("Este módulo estará disponible próximamente")
        return None
    
    def get_available_modules(self) -> list:
        """Retorna lista de módulos disponibles."""
        return list(self._modules.keys())
    
    def is_module_available(self, module_name: str) -> bool:
        """Verifica si un módulo está disponible."""
        return module_name in self._modules