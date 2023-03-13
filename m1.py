from sermeasure import SerMeasure

class M1(SerMeasure):
    def __init__(self, name: str, port: str):
        self.name = name
        self.port = port
        self.m1 = 1
        self.n_meas = 1
        self.connected = self.is_open()
        
    def open(self):
        pass
    
    def is_open(self):
        return True
    
    def close(self):
        pass
    
    def GetMeasure(self, i: int):
        self.m1 += 1
        return self.m1
    
    def GetUnit(self, i: int):
        return 'A'


class M2(SerMeasure):
    def __init__(self, name: str, port: str):
        self.name = name
        self.port = port
        self.m2 = 2    
        self.n_meas = 3
        self.connected = self.is_open()
         
    def open(self):
        pass
    
    def is_open(self):
        return True
    
    def close(self):
        pass
    
    def GetMeasure(self, i: int):
        self.m2 += 1
        return self.m2
    
    def GetUnit(self, i: int):
        return 'B'
