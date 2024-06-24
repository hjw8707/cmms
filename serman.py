import serial
import serial.tools.list_ports
from sermeasure import SerMeasure
from sermeasure_list import *

class SerMan:
    def __init__(self):
        self.load_ports()
    
    def load_ports(self):
        self.ports = []
        for port in sorted(serial.tools.list_ports.comports()):
            if port.device.find('ttyS') < 0:
                self.ports.append(port)
                
        
    def n_ports(self):
        return len(self.ports)
    
    def get_ports(self):
        return self.ports
    
    def get_port(self, i: int):
        try:
            return self.ports[i]
        except IndexError as e:
            print('No such an index.')
            return None

    def get_port_name(self, i: int):
        try:
            return self.ports[i].name
        except IndexError as e:
            print('No such an index.')
            return None

    def get_port_dev(self, i: int):
        try:
            return self.ports[i].device
        except IndexError as e:
            print('No such an index.')
            return None    

    def string_ports(self, port_only: bool = True):
        strs = []
        for port, desc, hwid in sorted(self.ports):
            if port_only:
                strs.append(f"{port}")
            else:
                strs.append(f"{port}: {desc} [{hwid}]")
        return strs

    def print_ports(self, port_only: bool = True):
        print('\n'.join(self.string_ports(port_only)))

    def find_port_class(self, port):
        print(f'Find a class for the port {port.name}.')
        if port is None:
            print('Cannot find such a port.')
            return None
        for cl in serm_class_list:
            try:
                print(f' Trying the class {cl.__name__}')
                dev = cl('port_check', port.device)
                if dev.is_this(): return cl
                #else: print(f' Not the class {cl.__name__}')
            except (serial.SerialException, TypeError, UnicodeDecodeError) as e:
                print(f"Error: {str(e)}")
                continue
        return None

    def find_ports_class(self):
        self.ports_class = [self.find_port_class(x) for x in self.ports]
        return self.ports_class

if __name__ == "__main__":
    sm = SerMan()
    sm.print_ports(False)
    print(sm.get_port_name(0))
    print(sm.get_port_dev(0))
    print(sm.find_ports_class())
