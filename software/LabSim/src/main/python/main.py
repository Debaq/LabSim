from venv import create
import numpy as np


class IntencityModel:
    """IntencityModel class
    Maneja la intensidad del estimulo según sea necesario
    """
    def __init__(self,_limits:dict, frequency:list=None) -> None:
        if frequency is None:
            self.list_frecuencies = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000]
        else:
            self.list_frecuencies = frequency
        self.limits = _limits
        self.frecuency = 1000
        self.intencity = 20
        self.exted_range = 20
        self.steps = 5
        self.load_limits(self.frecuency)
        self.range_intencity = self.create_range_intencity()


    def load_limits(self, frecuency:int) -> int:

        _limits = self.limits[frecuency]
        self.max_intencity = _limits[0]
        self.min_intencity = _limits[1]
        
    def next(self):
        idx_f = self.list_frecuencies.index(self.frecuency)
        self.frecuency = self.list_frecuencies[idx_f + 1]

    def prev(self):
        idx_f = self.list_frecuencies.index(self.frecuency)
        self.frecuency = self.list_frecuencies[idx_f - 1]

    def up(self):
        idx_prev = np.where(self.range_intencity == self.intencity)[0][0]
        self.intencity = self.range_intencity[idx_prev + 1]
    
    def down(self):
        idx_prev = np.where(self.range_intencity == self.intencity)[0][0]
        self.intencity = self.range_intencity[idx_prev - 1]

    def set_intencity(self, intencity:int):
        self.intencity = intencity
            
    def set_frecuency(self, frecuency:int):
        self.frecuency = frecuency

    def set_max_intencity(self, max_intencity:int):
        self.max_intencity = max_intencity

    def set_min_intencity(self, min_intencity:int):
        self.min_intencity = min_intencity

    def set_exted_range(self, extend_range:int):
        self.exted_range = extend_range

    def create_range_intencity(self, extend_range=False) -> int:
        if extend_range is False:
            max_value = self.max_intencity
        else:
            max_value = self.max_intencity + self.exted_range
        return  np.arange(self.min_intencity, max_value,self.steps)



limits = { 125: (-15, 120), 250 : (-15, 120), 500 : (-15, 120),
          1000 : (-15, 120), 2000 : (-15, 120), 3000 : (-15, 120),
          4000 : (-15, 120), 6000 : (-15, 120), 8000 : (-15, 120)}

model_inten = IntencityModel(limits)

model_inten.set_frecuency(500)



class DisplayChannel:
    def __init__(self) -> None:
        pass
