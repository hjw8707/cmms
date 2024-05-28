#!/usr/bin/python3

from sermeasure import SerMeasure, UnitType
from serial import Serial, serialutil
from serial.tools.list_ports import comports
    
##############################################
# class for reading the pressure from TPG36X
#
class BCG450(SerMeasure):
    vid_pid = (0x067B, 0x2303)
    ETX = b'\x03'
    CR  = b'\x0D'
    LF  = b'\x0A'
    ENQ = b'\x05'
    ACK = b'\x06'
    NAK = b'\x15'

    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.n_meas = 1
        self.type = UnitType.Pres
        self.open()

    def open(self):
        for port in comports():
            self.ser = Serial(self.port, timeout=1, write_timeout=1) # default is okay
            self.ser.write(b'\n')
            self.ser.reset_input_buffer()
            if self.ser and self.is_open():
                print('bcg450 opened')
                break
        else:
            self.ser = None
        
    def close(self):
        self.ser.close()
        
    def is_open(self):
        if self.ser == None:
            return False
        else:
            try:
                self.ser.read(1)
            except serialutil.SerialException:
                return False
            return True           
    
    def GetMeasure(self, i: int):
        if self.ser: return self.get_pr()
        else       : return 0
    
    def GetUnit(self, i: int):
        if self.ser: return self.get_unit()
        else       : return ''
    
    #########################################
    # read unit
    def get_unit(self):
        unit_name = [ 'mbar', 'Torr', 'Pa' ]
        s = self.get_str()
        unit = (s[2] >> 4) & 0x3
        return unit_name[unit]
    #########################################
    
    #########################################
    # read pressure
    def get_pr(self):
        unit_const = [ 12.5, 12.625, 10.5 ] # mbar, Torr, Pa
        s = self.get_str()
        unit = (s[2] >> 4) & 0x3
        return 10**((s[4]*256+s[5])/4000 - unit_const[unit])
    #########################################
    
    #########################################
    # read recent string
    def get_str(self):
        self.ser.reset_input_buffer()
        r = self.ser.read(18)
        for i in range(0,10):
            if r[i] == 7 and r[i+1] == 5:
                cs = sum(r[i+1:i+8]) % 256
                if r[i+8] == cs:
                    return r[i:i+9]
    #########################################            
                

    
########################################################################################################################        


if __name__=="__main__":
    bcg = BCG450()
    print(bcg.get_str())
    print('Pressure: %f %s' % (bcg.get_pr(), bcg.get_unit()))
