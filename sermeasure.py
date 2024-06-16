from abc import *
from serial import Serial
from enum import Enum, auto

class UnitType(Enum):
    Pres = auto()
    Temp = auto()
    Perc = auto()

# an abstract base class to declare methods for getting measurements via a serial port
class SerMeasure(metaclass=ABCMeta):

    # a constructor that initializes a name, port and n_meas attribute
    @abstractmethod
    def __init__(self, name: str, port: str):
        self.name = name
        self.port = port
        self.n_meas, self.n_state, self.n_status = 1, 1, 1
        self.type: list[UnitType] = [UnitType.Pres]
        pass
    
    # an abstract method that should be implemented by the subclass for opening a serial connection
    @abstractmethod
    def open(self):
        pass
    
    # an abstract method that should be implemented by the subclass for checking if the serial connection is open 
    @abstractmethod
    def is_open(self):
        pass

    @abstractmethod
    def is_this(self):
        return True or False
        pass
    
    # an abstract method that should be implemented by the subclass for closing the serial connection    
    @abstractmethod
    def close(self):
        pass
    
    # an abstract method that should be implemented by the subclass to get a measurement of a specific index i
    @abstractmethod
    def GetMeasure(self, i: int):
        if i >= self.n_meas: return 0
        pass

    # an abstract method that should be implemented by the subclass to get the unit of a specific index i
    @abstractmethod    
    def GetUnit(self, i: int):
        if i >= self.n_meas: return ''
        pass

    @abstractmethod
    def GetStateName(self, i: int):
        if i >= self.n_state: return 'name'
        pass

    @abstractmethod
    def GetState(self, i: int):
        if i >= self.n_state: return ''
        pass

    @abstractmethod
    def GetStatusName(self, i: int):
        if i >= self.n_status: return ''

    @abstractmethod
    def GetStatus(self, i: int):
        if i >= self.n_status: return False