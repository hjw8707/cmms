#!/usr/bin/python3

from sermeasure import SerMeasure, UnitType
from serial import Serial, SerialException, SerialTimeoutException
from serial.tools.list_ports import comports

###################################################
# class for reading the pressure from TIC100
#
# TIC100 should be connected via RS232 (RS232-USB converter)
class TIC100(SerMeasure):
    n_meas, n_state, n_status = 4, 1, 2

    def __init__(self, name: str, port: str):
        self.name: str   = name
        self.port: str   = port
        self.type: list[UnitType] = [UnitType.Pres, UnitType.Pres, UnitType.Pres, UnitType.Perc]
        self.type: list[UnitType] = self.n_meas * [UnitType.Pres]
        self.ok = False
        print(f'TIC100 with name: {self.name} and port: {self.port}  opened')

        self.verbose = False
        #self.open()
        self.model:     str = ''
        self.sw_ver:    str = ''
        self.ser_num:   str = ''
        self.picsw_ver: str = ''
        self.turbo_st:  int = 0
        self.back_st:   int = 0
        self.gauge_st = (0, 0, 0)
        self.relay_st = (0, 0, 0)

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
        self.status_querys()
        return self.ok
    
    def GetMeasure(self, i: int):
        if i >= self.n_meas: return 0
        if i == self.n_meas - 1:  return self.GetTMPSpeed()
        self.status_queryv()
        if self.gauge_st[i] == 0: return 0 # gauge is not connected
        return float(self.gauge_queryv(i+1).split(';')[0]) # gauge number convention (1 ~ 3)

    def GetUnit(self, i: int):
        if i >= self.n_meas: return ''
        if i == self.n_meas - 1: return '%'
        return 'Pa' # only pascal is used

    def GetStateName(self, i: int):  
        if i == 0: return 'TMP State'
        else: return ''

    def GetState(self, i: int):
        states = ['Stopped', 'Starting Delay',
                  'Stopping Short Delay', 'Stopping Normal Delay',
                  'Running', 'Accelerating',
                  'Fault Braking', 'Braking' ]
        if i == 0:
            return states[self.GetTMPStatus()]
        else: return ''

    def GetStatusName(self, i: int):
        statusnames = ['TMP Normal', 'TMP Standby' ]
        return statusnames[i]
    
    def GetStatus(self, i: int):
        if i == 0: return self.GetTMPNormal()
        if i == 1: return self.GetTMPStandby()
        return True

    def GetTMPStatus(self):
        self.status_queryv() 
        return int(self.turbo_st)
    
    def GetTMPSpeed(self):
        return float(self.tspeed_queryv().split(';')[0]) # speed in %

    def GetTMPNormal(self):
        ans = self.send_queryv(907)
        if ans is None: return False
        if   int(ans.split(';')[0]) == 0: return False
        elif int(ans.split(';')[0]) == 4: return True
        else: return False

    def GetTMPStandby(self):
        ans = self.send_queryv(908)
        if ans is None: return False
        if   int(ans.split(';')[0]) == 0: return False
        elif int(ans.split(';')[0]) == 4: return True
        else: return False        

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

    def turbo_queryv(self):
        ans = self.send_queryv(904)
        if ans is None: return False
        status = [x.strip() for x in ans.split(';')] # Pump status - state; alert ID; priority
        self.turbo_status = status[0]
        self.alert = status[1]
        return True
    
    def tspeed_queryv(self):
        data = self.send_queryv(905)
        if data is None: return 0.
        return data
    
    def tnormal_queryv(self):
        data = self.send_queryv(907)
        if data is None: return 0.
        return data

    def tstandby_queryv(self):
        data = self.send_queryv(908)
        if data is None: return 0.
        return data     

    def gauge_queryv(self, i: int): # i = 1, 2, 3
        if i < 1 or i > 3: return 0. # Error
        data = self.send_queryv(912+i)
        if data is None: return 0.
        return data
    
    #############################################################################
    def send_gcommand(self, oid: int, m: int):
        if not self.open(): return False
        try:
            self.ser.write( bytes('!C' + str(oid) + ' ' + str(m) + '\r', 'utf8') )
            answer = self.ser.read_until(b'\r').decode().rstrip() # return response from the unit
            if self.verbose: print("The receieved command is: ",answer)
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in send_gcommand: {str(e)}")
            self.ok = False
            self.close()
            return False
        self.close()        
        if answer.index('*C') != 0:
            self.ok = False
            return False
        oid_a, r = list(map(int, answer[answer.index('*C')+2:].split()))
        if oid_a != oid or r != 0:
            self.ok = False
            return False
        self.ok = True
        return True

    def send_scommand(self, oid: int, data: str):
        if data == '': return False
        if not self.open(): return False
        try:
            self.ser.write( bytes('!S' + str(oid) + ' ' + data + '\r', 'utf8') )
            answer = self.ser.read_until(b'\r').decode().rstrip() # return response from the unit
            if self.verbose: print("The receieved command is: ",answer)
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in send_scommand: {str(e)}")
            self.ok = False
            self.close()
            return False
        self.close()
        if answer.index('*S') != 0:
            self.ok = False
            return False
        oid_a, r = list(map(int, answer[answer.index('*S')+2:].split()))
        if oid_a != oid or r != 0:
            self.ok = False
            return False
        self.ok = True
        return True

    def send_querys(self, oid: int):
        if not self.open(): return None
        try:
            self.ser.write( bytes('?S' + str(oid) + '\r', 'utf8') )
            #print("The sent command is: ",command)
            answer = self.ser.read_until(b'\r').decode().rstrip() # return response from the unit
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in send_querys: {str(e)}")
            self.ok = False
            self.close()
            return None
        self.close()
        if answer == '' or answer.index('=S') != 0:
            print(f"Error in send_querys: No available answer")
            self.ok = False
            return None
        answers = answer[answer.index('=S')+2:].split()
        oid_a = int(answers[0])
        data = answers[1]
        if oid_a != oid or data == '':
            self.ok = False
            return None
        self.ok = True
        return data

    def send_queryv(self, oid: int):
        if not self.open(): return None
        try:
            self.ser.write( bytes('?V' + str(oid) + '\r', 'utf8') )
            #print("The sent command is: ",command)
            answer = self.ser.read_until(b'\r').decode().rstrip()
        # return response from the unit
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in send_queryv: {str(e)}")
            self.ok = False
            self.close()
            return None
        self.close()
        if answer.index('=V') != 0:
            self.ok = False
            return None
        answers= answer[answer.index('=V')+2:].split()
        oid_a = int(answers[0])
        data = answers[1]
        if oid_a != oid or data == '':
            self.ok = False
            return None
        self.ok = True
        return data
    #############################################################################
