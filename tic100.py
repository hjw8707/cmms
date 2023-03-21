#!/usr/bin/python3

from sermeasure import SerMeasure, UnitType
from serial import Serial
from serial.tools.list_ports import comports

###################################################
# class for reading the pressure from TIC100
#
# TIC100 should be connected via RS232 (RS232-USB converter)
class TIC100(SerMeasure):
    vid_pid = (0x0403, 0x6001) # need to be revised
    ETX = b'\x03'
    CR  = b'\x0D'
    LF  = b'\x0A'
    ENQ = b'\x05'
    ACK = b'\x06'
    NAK = b'\x15'

    def __init__(self, name: str, port: str):
        self.name: str   = name
        self.port: str   = port
        self.n_meas: int = 3
        self.type = UnitType.Pres
        self.open()
        self.model:     str = ''
        self.sw_ver:    str = ''
        self.ser_num:   str = ''
        self.picsw_ver: str = ''
        self.turbo_st:  int = 0
        self.back_st:   int = 0
        self.gauge_st = (0, 0, 0)
        self.relay_st = (0, 0, 0)

    def open(self):
        for port in comports():
            if (port.vid, port.pid) == self.vid_pid:
                self.ser = Serial(self.port, timeout=1, write_timeout=1) # default is okay
                self.ser.write(b'\n')
                self.ser.reset_input_buffer()
                if self.ser and self.is_open():
                   print('tic opened')
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
                r = self.status_querys()
            except OSError:
                return False
            return r 
    
    def GetMeasure(self, i: int):
        if i >= self.n_meas: return 0
        self.status_queryv()
        if self.gauge_st[i] == 0: return 0 # gauge is not connected
        return float(self.gauge_queryv(i+1).split(';')[0]) # gauge number convention (1 ~ 3)

    def GetUnit(self, i: int):
        if i >= self.n_meas: return ''
        return 'Pa' # only pascal is used
    
    def status_querys(self): # System string
        ans = self.send_querys(902)
        if ans is None: return False
        status = [x.strip() for x in ans.split(';')] # TIxxx; SW Ver; Ser Num; PIC SW ver
        self.model     = status[0]
        self.sw_ver    = status[1]
        self.ser_num   = status[2]
        self.picsw_ver = status[3]
        return True
    
    def status_queryv(self): # system status (True / False)
        ans = self.send_queryv(902)
        if ans is None:
            return False
        status = list(map(int, ans.split(';')))
        self.turbo_st, self.back_st, *gauge_relay_st = status
        self.gauge_st = gauge_relay_st[:3]
        self.relay_st = gauge_relay_st[3:]
        return True
    
    def gauge_queryv(self, i: int): # i = 1, 2, 3
        if i < 1 or i > 3: return 0. # Error
        data = self.send_queryv(912+i)
        if data is None: return 0.
        return data
    
    #############################################################################
    def send_gcommand(self, oid: int, m: int):
        self.ser.write( bytes('!C' + str(oid) + ' ' + str(m) + '\r', 'utf8') )
        #print("The sent command is: ",command)
        answer = self.ser.read_until(b'\r').decode().rstrip() # return response from the unit
        if answer.index('*C') != 0:
            return False
        oid_a, r = list(map(int, answer[answer.index('*C')+2:].split()))
        if oid_a != oid or r != 0:
            return False
        return True

    def send_scommand(self, oid: int, data: str):
        if data == '': return False
        self.ser.write( bytes('!S' + str(oid) + ' ' + data + '\r', 'utf8') )
        #print("The sent command is: ",command)
        answer = self.ser.read_until(b'\r').decode().rstrip() # return response from the unit
        if answer.index('*S') != 0:
            return False
        oid_a, r = list(map(int, answer[answer.index('*S')+2:].split()))
        if oid_a != oid or r != 0:
            return False
        return True

    def send_querys(self, oid: int):
        self.ser.write( bytes('?S' + str(oid) + '\r', 'utf8') )
        #print("The sent command is: ",command)
        answer = self.ser.read_until(b'\r').decode().rstrip() # return response from the unit
        if answer.index('=S') != 0:
            return None
        answers= answer[answer.index('=S')+2:].split()
        oid_a = int(answers[0])
        data = answers[1]
        if oid_a != oid or data == '':
            return None
        return data

    def send_queryv(self, oid: int):
        self.ser.write( bytes('?V' + str(oid) + '\r', 'utf8') )
        #print("The sent command is: ",command)
        answer = self.ser.read_until(b'\r').decode().rstrip()
        # return response from the unit
        if answer.index('=V') != 0:
            return None
        answers= answer[answer.index('=V')+2:].split()
        oid_a = int(answers[0])
        data = answers[1]
        if oid_a != oid or data == '':
            return None
        return data
    #############################################################################
