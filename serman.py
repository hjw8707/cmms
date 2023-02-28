import serial.tools.list_ports

class SerMan:
    def __init__(self):
        self.load_ports()
    
    def load_ports(self):
        self.ports = sorted(serial.tools.list_ports.comports())
        
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

if __name__ == "__main__":
    sm = SerMan()
    sm.print_ports(False)
    print(sm.get_port_name(0))
    print(sm.get_port_dev(0))