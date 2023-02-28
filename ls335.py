#!/usr/bin/python3

from lakeshore import Model335, generic_instrument
from sermeasure import SerMeasure

class LS335(SerMeasure):
    chs = ['A', 'B']
    
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.open()

    def open(self):
        try:
            self.tc = Model335(com_port=self.port, baud_rate=57600)
            print('ls335 opened')
        except generic_instrument.InstrumentException:
            self.tc = None
    
    def is_open(self):
        if self.tc == None:
            return False
        else:
            try:
                r = self.tc.query('*IDN?')
            #except (OSError, generic_instrument.InstrumentException):
            except OSError:
                return False
            except generic_instrument.InstrumentException:
                return True
            return True
    
    def close(self):
        if self.tc:  del self.tc

    def GetMeasure(self, i: int):
        return self.get_temp(self.chs[i])
    
    def GetUnit(self, i: int):
        return 'K'

    def get_mod_no(self):
        return self.tc.model_number

    def get_ser_no(self):
        return self.tc.serial_number    

    ############################################################
    # get temperature
    #
    # ch = channel (A, B, C, D, D2, D3, D4, D5)
    # unit = 0 (Kelvin), 1 (Celcius), 2 (Sensor)
    #
    # return = temperature
    def get_temp(self, ch, unit=0):
        if   unit == 0: return float(self.tc.query('KRDG? %s' % ch))
        elif unit == 1: return float(self.tc.query('CRDG? %s' % ch))
        elif unit == 2: return float(self.tc.query('SRDG? %s' % ch))
        else:           return None
    ############################################################        

    ############################################################
    # get temperature for all ch
    #
    # unit = 0 (Kelvin), 1 (Celcius), 2 (Sensor)
    #
    # return = temperature array [A, B, C, D, D2, D3, D4, D5]
    def get_temp_all(self, unit=0):
        if   unit == 0: return [float(x) for x in self.tc.query('KRDG? 0').split(',')]
        elif unit == 1: return [float(x) for x in self.tc.query('CRDG? 0').split(',')]
        elif unit == 2: return [float(x) for x in self.tc.query('SRDG? 0').split(',')]
        else:           return None
    ############################################################        

    ############################################################
    # get heater output
    #
    # ch = channel (1, 2)
    #
    # return = heater output in %
    def get_heater(self, ch = 1):
        return float(self.tc.query('HTR? %d' % ch))
    ############################################################        

    ############################################################
    # get heater status
    #
    # ch = channel (1, 2)
    #
    # return = heater status
    #           0 = no error
    #           1 = heater open load
    #           2 = heater short for output 1 or compliance for output 2
    def get_heater_status(self, ch = 1):
        return int(self.tc.query('HTRST? %d' % ch))
    ############################################################        

    ############################################################
    # get heater manual output
    #
    # ch = channel (1, 2)
    #
    # return = heater manual output in %
    def get_manual(self, ch = 1):
        return float(self.tc.query('MOUT? %d' % ch))
    ############################################################

    ############################################################
    # set heater manual output
    #
    # ch = channel (1, 2)
    #
    def set_manual(self, val, ch = 1):
        self.tc.command('MOUT %d,%f' % (ch, val))
    ############################################################        

    ############################################################
    # get heater range
    #
    # ch = channel (1, 2)
    #
    # return = heater range
    #          0 = off, 1 = range 1, 2 = range 2, 3 = range 3
    #          4 = range 4, 5 = range 5
    def get_range(self, ch = 1):
        return int(self.tc.query('RANGE? %d' % ch))
    ############################################################

    ############################################################
    # set heater range
    #
    # ch = channel (1, 2)
    # val = 0 ~ 5
    def set_range(self, val, ch = 1):
        self.tc.command('RANGE %d,%d' % (ch, val))
    ############################################################        

    ############################################################
    # get reading status
    #
    # ch = channel (A, B, C, D, D2, D3, D4, D5)
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
        return bin(int(self.tc.query('RDGST? %s' % ch)))
    ############################################################        

    
    ############################################################
    # get setpoint
    #
    # ch = channel (1, 2)
    #
    # return = set point
    def get_setpoint(self, ch = 1):
        return float(self.tc.query('SETP? %d' % ch))
    ############################################################

    ############################################################
    # set setpoint
    #
    # ch = channel (1, 2)
    #
    def set_setpoint(self, val, ch = 1):
        self.tc.command('SETP %d,%f' % (ch, val))
    ############################################################   

    ############################################################
    # set output mode
    #
    # ch = channel (1, 2)
    #
    def set_outputmode(self, ch, mode, inp, power):
        self.tc.command('OUTMODE %d,%d,%d,%d' % (ch, mode, inp, power))
    ############################################################   

    ############################################################
    # get output mode
    #
    # ch = channel (1, 2)
    #
    # return [mode, input, powerup enable]
    def get_outputmode(self, ch = 1):
        return [int(x) for x in self.tc.query('OUTMODE? %d' % ch).split(',')]
    ############################################################       

################################################################################

if __name__=="__main__":
    ls = LS335()
    
    print(ls.tc.query('*IDN?'))
    print(ls.tc.query('*IDN?'))
    print(ls.tc.query('*IDN?'))
    print('Model : ' + ls.get_mod_no())
    print('Serial: ' + ls.get_ser_no())
    print('TempA: ' + str(ls.get_temp('A')) + ' ' + 'K')

    
