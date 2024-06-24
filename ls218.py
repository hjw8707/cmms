#!/usr/bin/python3

from serial import Serial, PARITY_ODD, SerialException, SerialTimeoutException
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
        self.ser = None
        self.ok = False
        print(f'LS218 with name: {self.name} and port: {self.port}  opened')

        self.verbose = False

    def open(self):
        try:
            self.ser = Serial(self.port, baudrate=9600, 
                                bytesize=7, stopbits=1, parity=PARITY_ODD,
                                timeout=1, write_timeout=1) # default is okay
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
        self.query('*IDN?')
        return self.ok  
    
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
        a = self.query('*IDN?')
        return a.split(',') if a is not None else None
    ############################################################

    #################################
    def command(self, command):
        if not self.open(): return False
        if command == '': return False
        try: self.ser.write( bytes(command + '\r', 'utf8') ) # works better with older Python3 versions (<3.5)
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in command: {str(e)}")
            self.ok = False
            return False
        if self.verbose: print("The sent command is: ",command)
        self.ok = True
        return True

    def query(self, command):
        if self.command(command):
            try: r = self.ser.readline().decode('utf8').rstrip()
            except (SerialException, SerialTimeoutException) as e:
                print(f"Error in query: {str(e)}")
                self.ok = False
                self.close()
                return None
            self.close()
            if r == '': 
                print(f"Error in query: No answer")
                self.ok = False
                return None
            return r
        else:
            self.close()
            return None
    #################################

################################################################################

if __name__=="__main__":
    ls = LS218()
    
    print(ls.query('*IDN?'))
    print('Model : ' + ls.get_mod_no())
    print('Serial: ' + ls.get_ser_no())
    print('TempA: ' + str(ls.get_temp('A')) + ' ' + 'K')

    
