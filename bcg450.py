#!/usr/bin/python3

from sermeasure import SerMeasure, UnitType
from serial import Serial, SerialException, SerialTimeoutException
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
        self.n_meas, self.n_state, self.n_status = 1, 0, 0
        self.type = [UnitType.Pres]
        self.ser = None
        self.ok = False
        print(f'BCG450 with name: {self.name} and port: {self.port}  opened')

        self.pres = 0
        self.unit = 0 # 0 ~ 2 (mbar, torr, Pa)
        self.emis = 0 # 0 ~ 3 (emis. off, 25 uA, 5 mA, degas)
        self.err_dia = False
        self.err_pirani = False
        self.err_BA = False
        self.err_EL = False


    def open(self):
        try: 
            self.ser = Serial(self.port, timeout=1, write_timeout=1) # default is okay
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in open: {str(e)}")
            self.ser = None
            self.ok = False
        else: self.ok = True
        return self.ok
        
    def close(self):
        if self.ser is None: return
        try: self.ser.close()
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in close: {str(e)}")
        self.ser = None
        self.ok = False
        
    def is_open(self):
        return self.ok        
    
    def is_this(self):
        self.get_str()
        return self.ok

    def GetMeasure(self, i: int):
        return self.get_pr()
    
    def GetUnit(self, i: int):
        return self.get_unit()

    def GetStateName(self, i: int):  pass
    def GetState(self, i: int):      pass
    def GetStatusName(self, i: int): pass
    def GetStatus(self, i: int):     pass

    #########################################
    # read unit
    def get_unit(self):
        unit_name = [ 'mbar', 'Torr', 'Pa' ]
        self.get_str()
        return unit_name[self.unit] if self.ok else None
    #########################################
    
    #########################################
    # read pressure
    def get_pr(self):
        unit_const = [ 12.5, 12.625, 10.5 ] # mbar, Torr, Pa
        self.get_str()
        return 10**(self.pres/4000 - unit_const[self.unit]) if self.ok else None
    #########################################
    
    def set_unit(self, u):
        unit_name = [ 'mbar', 'Torr', 'Pa' ]
        try: ind = unit_name.index(u)
        except (ValueError) as e:
            print(f'Error in set_unit: {str(e)}')
            return
        self.send_str(bytes.fromhex('108E'), unit_name.index(u))

    def store_unit(self):
        self.send_str(bytes.fromhex('2007'), 0)        

    #########################################
    # read recent string
    def get_str(self):
        if not self.open(): return
        try:
            self.ser.reset_input_buffer()
            r = self.ser.read(18)
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in get_str: {str(e)}")
            self.ok = False
            return
        if len(r) < 18:
            print("Error in get_str: Shorter string")
            self.ok = False
            self.close()
            return
        for i in range(0,10):
            if r[i] == 7 and r[i+1] == 5:
                cs = sum(r[i+1:i+8]) % 256
                if r[i+8] != cs: continue
                # found the right string
                self.emis = r[i+2] & 0x3
                self.unit = (r[i+2] >> 4) & 0x3
                self.err_dia = ((r[i+3] & 0x1) == 0x1)
                self.err_pirani = ((r[i+3] & 0x4) == 0x4)
                self.err_BA = ((r[i+3] & 0x10) == 0x10)
                self.err_BL = ((r[i+3] & 0x40) == 0x40)
                self.pres = r[i+4]*256+r[i+5]
                self.ok = True
                self.close()
                return
        print("Error in get_str: Cannot find a good string")
        self.ok = False
        self.close()
    #########################################            

    #########################################
    # write recent string
    def send_str(self, comm, val):
        if not self.open(): return
        try:
            self.ser.reset_output_buffer()
            b = bytearray(bytes.fromhex('03'))
            b += bytes.fromhex(comm)
            b += val.to_bytes()
            b += sum(b[1:4]).to_bytes()
            self.ser.write(b)
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in send_str: {str(e)}")
            self.ok = False
        else:
            self.ok = True
        self.close()
########################################################################################################################        
if __name__=="__main__":
    bcg = BCG450()
    print(bcg.get_str())
    print('Pressure: %f %s' % (bcg.get_pr(), bcg.get_unit()))
