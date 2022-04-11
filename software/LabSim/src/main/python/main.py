import numpy as np





class IntencityModel:
    """IntencityModel class
    Maneja la intensidad del estimulo según sea necesario    
    """
    def __init__(self):
        pass

    def set_up(self, step=1):
        pass
    
    def set_down(self, step=1):
        pass
    
    def get(self) -> int:
        pass
    
    def set_max_intencity(self, max_intencity:int):
        pass
    
    def set_min_intencity(self, min_intencity:int):
        pass

    def intencity(self, up:bool, prev:int, extend_range=False) -> int:
        max_value = 100 if extend_range else 120
        values = np.arange(-15, max_value,5)
        idx_prev = np.where(values == prev)[0][0]
        idx_new = idx_prev + 1 if up else idx_prev - 1
        return values[idx_new]





a = intencity(True, 20)

print(a)

class DisplayChannel:
    def __init__(self) -> None:
        pass
