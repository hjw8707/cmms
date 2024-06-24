#!/usr/bin/python3

from sermeasure import UnitType, SerMeasure
from serial import Serial, SerialException, SerialTimeoutException
from serial.tools.list_ports import comports

###################################################
# class for reading the pressure from VSM7XX
#
class VSM7XX(SerMeasure):

    def __init__(self, name, port, _address = 1):
        self.name = name
        self.port = port
        self.n_meas, self.n_state, self.n_status = 1, 0, 0
        self.type: list[UnitType] = self.n_meas * [UnitType.Pres]
        self.ok = False
        print(f'VSN7XX with name: {self.name} and port: {self.port}  opened')

        self.verbose = False

        self.address = _address

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
        self.get_prod_name()
        return self.ok
    
    def GetMeasure(self, i: int):
        r = self.get_pr()
        if   r == '' or r == None or r == 'UR': return 0
        if   r == 'OR': return 1e3
        return float(r)
    
    def GetUnit(self, i: int):
        return 'mbar'

    def GetStateName(self, i: int):  pass
    def GetState(self, i: int):      pass
    def GetStatusName(self, i: int): pass
    def GetStatus(self, i: int):     pass   
    
    #########################################
    # pressure of gauge in mbar
    #
    # return:
    #      float = pressure
    #        UR  = under range
    #        OR  = over range
    def get_pr(self):
        return self.read_command('MV')
    #########################################

    #########################################
    # pressure unit
    #
    def get_dis_unit(self):
        return self.read_command('DU')
    #########################################

    #########################################
    # display orientation
    #
    def get_dis_ori(self):
        return self.read_command('DO')
    #########################################

    #########################################
    # display orientation
    #
    def set_dis_ori(self, flag_normal: bool = True):
        r = self.write_command('DO', '0' if flag_normal else '1')
        return r
    #########################################

    #########################################
    # unit type
    def get_type(self):
        return self.read_command('TD')
    #########################################

    #########################################
    # product name
    def get_prod_name(self):
        return self.read_command('PN')
    #########################################

    #########################################
    # serial number device
    def get_serial_no_dev(self):
        return self.read_command('SD')
    #########################################    

    #########################################
    # serial number head
    def get_serial_no_head(self):
        return self.read_command('SH')
    #########################################    
    
########################################################################################################################        
    def read_command(self, command: str):
        if not self.open(): return None
        if command == '': return None
        # ADR (0XX) + AC + CMD (XX) + Length (00) + CheckSum + CR
        seq = ('%03d' % self.address) + '0' + command + '00'
        seq = seq + chr(sum([ord(x) for x in seq]) % 64 + 64)
        try: self.ser.write( bytes(seq + '\r', 'utf8') ) # works better with older Python3 versions (<3.5)
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in read_command: {str(e)}")
            self.ok = False
            self.close()
            return None
        if self.verbose: print("The sent sequence is: ",seq) 
        try: answer = self.ser.read_until(b'\r').rstrip() # return response from the unit
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in read_command: {str(e)}")
            self.ok = False
            self.close()
            return None
        if self.verbose: print("The received command is: ",answer)
        try: dlen = int(answer[6:8])
        except (IndexError, ValueError) as e:
            print(f"Error in read_command: {str(e)}")
            self.ok = False
            self.close()
            return None
        self.ok = True
        self.close()        
        if answer[3] == 49:
            if dlen > 0: return answer[8:8+dlen].decode()
            else:        return ''
        else: 
            print('read_command: error in communication')
            return None

    def write_command(self, command: str, data: str):
        if not self.open(): return None
        if command == '': return None
        # ADR (0XX) + AC + CMD (XX) + Length (00) + CheckSum + CR
        seq = ('%03d' % self.address) + '2' + command + ('%02d' % len(data)) + data
        seq = seq + chr(sum([ord(x) for x in seq]) % 64 + 64)
        try: self.ser.write( bytes(seq + '\r', 'utf8') ) # works better with older Python3 versions (<3.5)
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in write_command: {str(e)}")
            self.ok = False
            self.close()
            return None
        if self.verbose: print("The sent sequence is: ",seq) 
        try: answer = self.ser.read_until(b'\r').rstrip() # return response from the unit
        except (SerialException, SerialTimeoutException) as e:
            print(f"Error in write_command: {str(e)}")
            self.ok = False
            self.close()
            return None
        self.close()
        if self.verbose: print("The received command is: ",answer)
        try: dlen = int(answer[6:8])
        except (IndexError, ValueError) as e:
            print(f"Error in write_command: {str(e)}")
            self.ok = False
            return None    
        self.ok = True
        if answer[3] == 51: 
            if dlen > 0: return answer[8:8+dlen].decode()
            else:        return ''
        else: 
            print('write_command: error in communication')
            return None     
########################################################################################################################        

if __name__=="__main__":
    vsm = VSM7XX(name='vsm', port='/dev/cu.usbserial-AB0PBQ3U')
    vsm.verbose = True
    print(vsm.get_type())
    #print(vsm.GetMeasure(0))
    #print(vsm.GetUnit(0))

