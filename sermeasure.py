from abc import *
from serial import Serial

class SerMeasure(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, name: str, port: str):
        self.name = name
        self.port = port
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
        pass

    @abstractmethod    
    def GetUnit(self, i: int):
        pass