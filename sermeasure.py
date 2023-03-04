from abc import *
from serial import Serial

class SerMeasure(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, name: str, port: str):
        self.name = name
        self.port = port
        self.n_meas = 1
        pass
    
    @abstractmethod
    def open(self):
        pass
    
    @abstractmethod
    def is_open(self):
        pass
    
    @abstractmethod
    def close(self):
        pass
    
    @abstractmethod
    def GetMeasure(self, i: int):
        if i >= self.n_meas: return 0
        pass

    @abstractmethod    
    def GetUnit(self, i: int):
        if i >= self.n_meas: return ''
        pass