#!/usr/bin/python3

from serial import Serial, PARITY_ODD
from serial.tools.list_ports import comports
from sermeasure import SerMeasure, UnitType

class LS218(SerMeasure):
    vid_pid = (0x067B, 0x2303)
    chs = [str(x) for x in [*range(1,9)]]

    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.n_meas, self.n_state, self.n_status = 8, 0, 0
        self.type = self.n_meas * [UnitType.Temp]
        self.open()

    def open(self):
        for port in comports():
            if (port.vid, port.pid) == self.vid_pid:
                self.ser = Serial(self.port, baudrate=9600, 
                                  bytesize=7, stopbits=1, parity=PARITY_ODD,
                                  timeout=1, write_timeout=1) # default is okay
                self.ser.write(b'\n')
                self.ser.reset_input_buffer()
                if self.ser and self.is_open():
                   print('ls218 opened')
                   break
        else:
            self.ser = None
    
    def is_open(self):
        if self.ser == None:
            return False
        else:
            try:
                r = self.query('*IDN?')
            except OSError:
                return False
            if len(r) < 1 or r[0] == '':
                return False
            return True    
    
    def close(self):
        self.ser.close()

    def GetMeasure(self, i: int):
        return self.get_temp(self.chs[i])
    
    def GetUnit(self, i: int):
        return 'K'

    def GetStateName(self, i: int):  pass
    def GetState(self, i: int):      pass
    def GetStatusName(self, i: int): pass
    def GetStatus(self, i: int):     pass

    def get_mod_no(self):
        return self.query_idn()[1]

    def get_ser_no(self):
        return self.query_idn()[2]   

    ############################################################
    # get temperature
    #
    # ch = channel (1 ~ 8)
    # unit = 0 (Kelvin), 1 (Celcius), 2 (Sensor)
    #
    # return = temperature
    def get_temp(self, ch, unit=0):
        if   unit == 0: return float(self.query('KRDG? %s' % ch))
        elif unit == 1: return float(self.query('CRDG? %s' % ch))
        elif unit == 2: return float(self.query('SRDG? %s' % ch))
        else:           return None
    ############################################################        

    ############################################################
    # get temperature for all ch
    #
    # unit = 0 (Kelvin), 1 (Celcius), 2 (Sensor)
    #
    # return = temperature array [1 ~ 8]
    def get_temp_all(self, unit=0):
        if   unit == 0: return [float(x) for x in self.query('KRDG? 0').split(',')]
        elif unit == 1: return [float(x) for x in self.query('CRDG? 0').split(',')]
        elif unit == 2: return [float(x) for x in self.query('SRDG? 0').split(',')]
        else:           return None
    ############################################################            

    ############################################################
    # get reading status
    #
    # ch = channel (1 ~ 8)
    #
    # return = binary expression
    #          0b00000000
    #            ||||   |
    #            ||||   invalid reading
    #            |||temp underrange
    #            ||temp overrange
    #            |sensor utnits zero
    #            sensor units overrange
    def get_read_status(self, ch):
        return bin(int(self.query('RDGST? %s' % ch)))
    ############################################################        
     

    ############################################################
    # Query Identification
    # *IDN? <manufacturer>,<modelnumber>,<serialnumber>,<firmwaredate>
    # Format: LSCI,MODEL218S,aaaaaa,nnnnnn[term]
    #
    # return [<manufacturer>,<modelnumber>,<serialnumber>,<firmwaredate>]
    def query_idn(self):
        return self.query('*IDN?').split(',')
    ############################################################

    #################################
    def command(self, command=''):
        if command == '': return False
        self.ser.write( bytes(command + '\r', 'utf8') ) # works better with older Python3 versions (<3.5)
        #print("The sent command is: ",command)
        #self.ser.readline() # read out echoed command
        return True

    def query(self, command=''):
        if self.command(command):
            return self.ser.readline().decode('utf8').rstrip()
        else: return ''
    #################################

################################################################################

if __name__=="__main__":
    ls = LS218()
    
    print(ls.query('*IDN?'))
    print('Model : ' + ls.get_mod_no())
    print('Serial: ' + ls.get_ser_no())
    print('TempA: ' + str(ls.get_temp('A')) + ' ' + 'K')

    
