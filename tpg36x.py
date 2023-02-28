#!/usr/bin/python3

from sermeasure import SerMeasure
from serial import Serial
from serial.tools.list_ports import comports

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
        self.open()

    def open(self):
        for port in comports():
            if (port.vid, port.pid) == self.vid_pid:
                self.ser = Serial(self.port, timeout=1, write_timeout=1) # default is okay
                self.ser.write(b'\n')
                self.ser.reset_input_buffer()
                if self.ser and self.is_open():
                   print('tpg opened')
                   break
        else:
            self.ser = None
        
    def close(self):
        self.ser.close()

    def GetMeasure(self, i: int):
        if self.ser: return self.get_pr1()
        else       : return 0
    
    def GetUnit(self, i: int):
        if self.ser: return self.get_uni()
        else       : return ''

    def is_open(self):
        if self.ser == None:
            return False
        else:
            try:
                r = self.comm_ayt()
            except OSError:
                return False
            if len(r) < 1 or r[0] == '':
                return False
            return True        
    
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
        if r[0] == '':
            return 0
        return float(r[1])
    #########################################

    #########################################
    # pressure unit
    #
    def get_uni(self):
        units = ['mbar', 'Torr', 'Pa', 'Micron', 'hPa', 'Volt' ]
        r = self.comm_uni()
        if r[0] == '':
            return ''
        return units[int(r[0])]
    #########################################

    #########################################
    # unit type
    def get_type(self):
        r = self.comm_ayt()
        if r[0] == '': return ''
        return r[0]
    #########################################

    #########################################
    # model no
    def get_mod_no(self):
        r = self.comm_ayt()
        if r[0] == '': return ''
        return r[1]
    #########################################

    #########################################
    # serial no
    def get_ser_no(self):
        r = self.comm_ayt()
        if r[0] == '': return ''
        return r[2]
    #########################################

    
########################################################################################################################        
    def send_command(self, command=''):
        if command == '': return False
        self.ser.write( bytes(command + '\r', 'utf8') ) # works better with older Python3 versions (<3.5)
        #print("The sent command is: ",command)
        #self.ser.readline() # read out echoed command
        answer = self.ser.readline().rstrip() # return response from the unit
        #print("The received command is: ",answer)
        if answer == b'': return False
        if answer[0] == self.NAK: return False
        else: return True

    def send_query(self):
        self.ser.write(self.ENQ)
        return self.ser.readline().decode('utf8').rstrip() # return as a string

    def send_command_with_query(self, command=''):
        if self.send_command(command):
            return self.send_query()
        else: return ''

    def comm_ayt(self):
        return self.send_command_with_query('AYT').split(',')

    def comm_pr1(self):
        return self.send_command_with_query('PR1').split(',')

    def comm_uni(self):
        return self.send_command_with_query('UNI').split(',')    
########################################################################################################################        


if __name__=="__main__":
    tpg = TPG(ser_num='AD0K7AX9')
    print('Open? : ' + str(tpg.is_open()))
    print('Type  : ' + tpg.get_type())
    print('Model : ' + tpg.get_mod_no())
    print('Serial: ' + tpg.get_ser_no())
    print('Gauge1: ' + str(tpg.get_pr1()) + ' ' + tpg.get_uni())

