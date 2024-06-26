from sermeasure import UnitType, SerMeasure

class M1(SerMeasure):
    n_meas, n_state, n_status = 1, 0, 0
    def __init__(self, name: str, port: str):
        self.name = name
        self.port = port
        self.m1 = 1
        self.type = [UnitType.Pres]

        self.ok = False
        print(f'M1 with name: {self.name} and port: {self.port}  opened')

        
    def open(self):
        pass
    
    def is_open(self):
        return True
    
    def is_this(self):
        return self.ok  
    
    def close(self):
        pass
    
    def GetMeasure(self, i: int):
        self.m1 += 1
        return self.m1

    def GetUnit(self, i: int):
        return 'Torr'

    def GetStateName(self, i: int):
        pass
    
    def GetState(self, i: int):
        pass

    def GetStatusName(self, i: int):
        pass

    def GetStatus(self, i: int):
        pass


class M2(SerMeasure):
    n_meas, n_state, n_status = 3, 1, 1
    def __init__(self, name: str, port: str):
        self.name = name
        self.port = port
        self.m2 = 2    
        self.type = self.n_meas * [UnitType.Temp]

        self.ok = False
        print(f'M2 with name: {self.name} and port: {self.port}  opened')

    def open(self):
        pass
    
    def is_open(self):
        return True
    
    def is_this(self):
        return self.ok  
    
    def close(self):
        pass
    
    def GetMeasure(self, i: int):
        self.m2 += 1
        return self.m2

    def GetUnit(self, i: int):
        return 'K'

    def GetStateName(self, i: int):
        return 'M2 TMP'

    def GetState(self, i: int):
        return 'State'

    def GetStatusName(self, i: int):
        return 'Status'

    def GetStatus(self, i: int):
        return True

class M3(SerMeasure):
    n_meas, n_state, n_status = 2, 1, 1
    def __init__(self, name: str, port: str):
        self.name = name
        self.port = port
        self.m3 = 3   
        self.type = [UnitType.Temp, UnitType.Perc]        

        self.ok = False
        print(f'M3 with name: {self.name} and port: {self.port}  opened')

    def open(self):
        pass
    
    def is_open(self):
        return True
    
    def is_this(self):
        return self.ok  
    
    def close(self):
        pass
    
    def GetMeasure(self, i: int):
        self.m3 += 1
        return self.m3

    def GetUnit(self, i: int):
        if i == 0: return 'K'
        else: return '%'

    def GetStateName(self, i: int):
        return 'M3 TMP'

    def GetState(self, i: int):
        return 'Good'

    def GetStatusName(self, i: int):
        return 'M3 Good'

    def GetStatus(self, i: int):
        return True
