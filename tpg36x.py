#!/usr/bin/python3

from sermeasure import UnitType, SerMeasure
from serial import Serial, SerialException, SerialTimeoutException
from serial.tools.list_ports import comports
from typing import Dict, List

###################################################
# class for reading the pressure from TPG36X
#
class TPG36X(SerMeasure):
    vid_pid = (0x0403, 0x6001)
    ETX = b'\x03'
    CR  = b'\x0D'
    LF  = b'\x0A'
    ENQ = b'\x05'
    ACK = b'\x06'
    NAK = b'\x15'

    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.n_meas, self.n_state, self.n_status = 2, 0, 0
        self.type: list[UnitType] = self.n_meas * [UnitType.Pres]

        self.ok = False
        self.verbose = False
        #self.open()

    def open(self):
        try: 
            self.ser = Serial(self.port, timeout=1, write_timeout=1) # default is okay
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in open: {str(e)}")
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
        return (self.get_type().startswith('TPG36'))

    def GetMeasure(self, i: int):
        if i == 0: r = self.get_pr1()
        else: r = self.get_pr2()
        return r
    
    def GetUnit(self, i: int):
        return self.get_uni()

    def GetStateName(self, i: int):  pass
    def GetState(self, i: int):      pass
    def GetStatusName(self, i: int): pass
    def GetStatus(self, i: int):     pass  
    
    #########################################
    # pressure of gauge 1
    #
    # return:
    #      float = pressure
    #         0  = error in data recieving
    #        -1  = under range
    #        -2  = over range
    #        -3  = sensor error
    #        -4  = sensor off
    #        -5  = no sensor
    #        -6  = idenfication error
    def get_pr1(self):
        r = self.comm_pr1()
        if r is None: return 0
        return float(r[1])
    
    def get_pr2(self):
        r = self.comm_pr1()
        if r is None: return 0
        return float(r[1])
    #########################################

    #########################################
    # pressure unit
    #
    def get_uni(self):
        units = ['mbar', 'Torr', 'Pa', 'Micron', 'hPa', 'Volt' ]
        r = self.comm_uni()
        if r is None: return ''
        return units[int(r[0])]
    #########################################

    #########################################
    # unit type
    def get_type(self) -> str:
        r = self.comm_ayt()
        if r is None: return ''
        return r[0]
    #########################################

    #########################################
    # model no
    def get_mod_no(self):
        r = self.comm_ayt()
        if r is None: return ''
        return r[1]
    #########################################

    #########################################
    # serial no
    def get_ser_no(self):
        r = self.comm_ayt()
        if r is None: return ''
        return r[2]
    #########################################

    
########################################################################################################################        
    def send_command(self, command, val: List[str] = []):
        if command == '': return False
        s = command
        if len(val) > 0: s += (',' + ','.join(val))
        try: self.ser.write( bytes(s + '\r', 'utf8') ) # works better with older Python3 versions (<3.5)
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in send_command: {str(e)}")
            self.ok = False
            return False
        if self.verbose: print("The sent command is: ",s)
        #self.ser.readline() # read out echoed command
        try: answer = self.ser.readline().rstrip() # return response from the unit
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in send_command: {str(e)}")
            self.ok = False
            return False
        if self.verbose: print("The received command is: ",answer)
        if answer == b'': 
            self.ok = False
            print(f"Error in send_command: Nothing is received")
            return False
        self.ok = True
        if answer[0] == self.NAK: return False
        else: return True

    def send_query(self):
        try: 
            self.ser.write(self.ENQ)
            a = self.ser.readline().decode('utf8').rstrip() # return as a string
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in send_query: {str(e)}")
            self.ok = False
            return None
        self.ok = True
        return a

    def send_command_with_query(self, command):
        if not self.open(): return None
        if self.send_command(command):
            r = self.send_query()
            self.close()
            return r
        else:
            self.close() 
            return None

    def comm_ayt(self):
        a = self.send_command_with_query('AYT')
        return a.split(',') if a is not None else None

    def comm_pr1(self):
        a = self.send_command_with_query('PR1')
        return a.split(',') if a is not None else None
     
    def comm_pr2(self):
        a = self.send_command_with_query('PR2')
        return a.split(',') if a is not None else None
    
    def comm_uni(self):
        a = self.send_command_with_query('UNI')
        return a.split(',') if a is not None else None
  ########################################################################################################################        


if __name__=="__main__":
    tpg = TPG36X(ser_num='AD0K7AX9')
    print('Open? : ' + str(tpg.is_open()))
    print('Type  : ' + tpg.get_type())
    print('Model : ' + tpg.get_mod_no())
    print('Serial: ' + tpg.get_ser_no())
    print('Gauge1: ' + str(tpg.get_pr1()) + ' ' + tpg.get_uni())

