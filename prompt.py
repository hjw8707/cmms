from prompt_toolkit import PromptSession, prompt, Application
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.key_binding import KeyBindings

import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, PointSettings

import time
import re
import threading
from typing import List, Dict

from sermeasure import SerMeasure
from sermeasure_list import *
from serman import SerMan

def is_url(text):
    url_pattern = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"
    return re.match(url_pattern, text) is not None

url_validator = Validator.from_callable(
    is_url, error_message='This input is not the URL format.',
    move_cursor_to_end=True)

def is_path(text):
    path_pattern = "^(?:[\\w]\\:|\\/)(\\/[a-z_\\-\\s0-9\\.]+)+\\.(\\/[a-z_\\-\\s0-9\\.]+)$"
    return re.match(path_pattern, text) is not None

path_validator = Validator.from_callable(
    is_path, error_message='This input is not the path format.',
    move_cursor_to_end=True)

def is_float(text):
    float_pattern = "^\\d+(\\.\\d+)?$"
    return re.match(float_pattern, text) is not None

float_validator = Validator.from_callable(
    is_float, error_message='This input is not a floating number.',
    move_cursor_to_end=True)

class ThreadSermeasure(threading.Thread):
    def __init__(self, serm: SerMeasure):
        super().__init__()
        self.dev = serm
        self.meas = []
        self.state = []
        self.status = []

    def run(self):
        self.meas = []
        self.state = []
        self.status = []
        for i in range(self.dev.n_meas): self.meas.append(self.dev.GetMeasure(i))
        for i in range(self.dev.n_state): self.state.append(self.dev.GetState(i))
        for i in range(self.dev.n_status): self.status.append(self.dev.GetStatus(i))

    
class InfluxSender():
    def __init__(self):
        self.t = 0
        self.running = True

    def set_influx_setting(self, url, token, org, bucket):
        self.url = url
        self.org = org
        self.bucket = bucket
        with open(token) as f:
            self.token = f.readline().rsplit()[0]

    def set_device_setting(self, freq, dev_list, tag_gen, tag_dev, tag_chan):
        self.freq = freq
        self.tag_gen = tag_gen
        self.dev_list = []
        self.tag_dev = []
        for tag, dev in zip(tag_dev, dev_list):
            if dev[2]: 
                self.dev_list.append(dev)
                self.tag_dev.append(tag)
        self.n_dev = len(self.dev_list)

    def job_test(self):
        self.running = True

        print(self.dev_list)
        devs = [x[1]('test', x[0]) for x in self.dev_list]
        while self.running:
            ths = [ThreadSermeasure(dev) for dev in devs]
            [th.start() for th in ths]
            [th.join() for th in ths]
            self.make_points(ths)
            #for th in ths: print(th.meas, th.status, th.state)
            time.sleep(self.freq)
        

    def write_test(self):
        try:
            write_client = influxdb_client.InfluxDBClient(url=self.url, token=self.token, org=self.org)
            write_api = write_client.write_api(write_options=SYNCHRONOUS)
        except:
            print('Error in InfluxSender')
            return
        value = 0
        self.running = True
        while self.running:
            value += 1
            point = (
                Point("measurement1")
                .tag("tagname1", "tagvalue1")
                .field("field1", value)
            )
            try: write_api.write(bucket=self.bucket, org=self.org, record=point)
            except:
                print('Error in InfluxSender')
                return
            time.sleep(self.freq) # separate points by 1 second

    def write_influx(self):
        pset = PointSettings()
        for k, v in self.tag_gen.items(): pset.add_default_tag(k, v)
        try:
            write_client = influxdb_client.InfluxDBClient(url=self.url, token=self.token, org=self.org)
            write_api = write_client.write_api(write_options=SYNCHRONOUS, point_settings=pset)
        except:
            print('Error in InfluxSender')
            return
        
        devs = [x[1](x[1].__name__, x[0]) for x in self.dev_list]
        while self.running:
            ths = [ThreadSermeasure(dev) for dev in devs]
            [th.start() for th in ths]
            [th.join() for th in ths]
            pts = self.make_points(ths)
            try: write_api.write(self.bucket, self.org, pts)
            except:
                print('Error in InfluxSender')
                return
            time.sleep(self.freq)

    def make_points(self, ths: List[ThreadSermeasure]) -> List[Point]:
        points = []
        for th, tag in zip(ths, self.tag_dev):
            ptm, pta, ptb = Point("Measure"), Point("State"), Point("Status")
            for k, v in tag.items(): 
                ptm = ptm.tag(k, v)
                pta = pta.tag(k, v)
                ptb = ptb.tag(k, v)
            points += [ptm.tag("dev", th.dev.name).tag("channel", i).field("value", float(m)) for i, m in enumerate(th.meas)]
            points += [pta.tag("dev", th.dev.name).tag("channel", i).field("value", m) for i, m in enumerate(th.state)]
            points += [ptb.tag("dev", th.dev.name).tag("channel", i).field("value", m) for i, m in enumerate(th.status)]
        return points
        #print(len(points), points)

class CMMSIS():
    
    def __init__(self):
        ########################################################
        # Parameter Variables
        self.influx_url = 'http://localhost:8086'
        self.influx_token = 'influx_token.txt'
        self.influx_org = 'CENS'
        self.influx_bucket = 'test'

        self.port_n = 0
        self.dev_n = 0
        self.sel_n = 0
        self.dev_list: List[List[str,SerMeasure,bool]] = [] #[['/dev/ttyUSB0', M1, True], ['/dev/ttyUSB1', M2, False]]

        self.tag_gen: Dict = {} #{'tagg':'t'}
        self.tag_dev: List[Dict] = [] #[{'taggen': 'tag1'}, {'taggen2': 'tag2'}]
        self.tag_chan: List[List[Dict]] = []

        self.freq = 1.0 # [sec]
        self.status = 0 # 0 = Idle, 1 = Running
        ########################################################

        ########################################################
        # 메뉴 항목을 정의합니다.
        self.main_menu_items = ['Influx Setting', 'Serial Setting', 'Tag Setting', 'Run', 'Exit']
        self.submenu_options = {
                'Influx Setting': ['URL', 'Token File', 'Organization', 'Bucket', 'Back'],
                'Serial Setting': ['Port Update', 'Device Scan', 'Select', 'Back'],
                'Tag Setting'   : ['General', 'Device', 'Channel', 'Back'],
                'Run':            ['Frequency', 'Start', 'Stop', 'Back'],
            }
        ########################################################
        # WordCompleter를 사용하여 자동 완성을 설정합니다.
        self.main_menu_completer = WordCompleter(self.main_menu_items + 
                                                 [str(i) for i in range(1, len(self.main_menu_items) + 1)], 
                                                 ignore_case=True)
        ########################################################

        self.session = PromptSession()
        #self.session.key_bindings = bindings
        self.sm = SerMan()
        self.sender = InfluxSender()
        self.job = threading.Thread()
        self.update_submenu_info()

    def update_submenu_info(self):
        self.submenu_info = {
                'Influx Setting': [self.influx_url, self.influx_token, self.influx_org, self.influx_bucket, ''],
                'Serial Setting': [f'{self.port_n} Ports', f'{self.dev_n} Available Devices', f'{self.sel_n} Selected Devices', ''],
                'Tag Setting' : None,
                'Run': [f'{self.freq} sec', ['Idle', 'Running'][self.status], '', '']}            

    def display_menu(self, menu_items, menu_infos = None, flag_idx = True, flag_title = False):
        print("\n", '=' * 30, 'CMMS: Influx Sender', '=' * 30)
        if flag_title:
            print(f"  {menu_items[0]:<20}")
            menu_items.pop(0)
        for idx, item in enumerate(menu_items, 1):
            if item == 'Back' or item == 'Exit': print(f"{0:>3}. {item:<20}", end = '')
            elif flag_idx: print(f"{idx:>3}. {item:<20}", end = '')
            else: print(f"  {item:<20}", end = '') 
            if menu_infos is not None and menu_infos[idx-1] != '':
                print(f': {menu_infos[idx-1]:<30}', end = '')
            print()
        print(' ' + ('=' * 81))

    def handle_option(self, menu_items, choice):
        if choice.isdigit():
            if int(choice) == 0:
                if 'Back' in menu_items: return 'Back'
                if 'Exit' in menu_items: return 'Exit'
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(menu_items):
                return menu_items[choice_idx]
        return choice

    def execution(self, choice):
        if choice == 'URL':
            self.influx_url = prompt('Input an URL of an influx server: ', default='http://grafmon.local:8086',
                                validator=url_validator, validate_while_typing=False)
        elif choice == 'Token File':
            self.influx_token = prompt('Input a file path for an influx token: ', default='influx_token.txt',
                                validator=path_validator, validate_while_typing=False)
        elif choice == 'Organization':
            self.influx_org = prompt('Input an organization of an influx server: ', default='CENS')
        elif choice == 'Bucket':
            self.influx_bucket = prompt('Input an bucket name of an influx server: ', default='CMMS')
        elif choice == 'Port Update':
            print( ' Updating the serial port information.')
            self.sm.load_ports()
            self.port_n = self.sm.n_ports()
            port_lists = self.sm.string_ports(False)
            for i, x in enumerate(port_lists, 1):
                print(f'  {i:>2}. {x}')
            print(f'  {self.port_n} ports found.')
        elif choice == 'Device Scan':
            dev_cl_list = self.sm.find_ports_class()
            self.dev_n = len(dev_cl_list) - dev_cl_list.count(None)
            port_lists = self.sm.string_ports()
            print( ' Scanning the serial port devices.')
            self.dev_list = []
            for i, (x, y) in enumerate(zip(port_lists, dev_cl_list), 1):
                if y is None: continue
                print(f'  {i:>2}. {x}: {y.__name__}')
                self.dev_list.append([x, y, False])
            print(f'  {self.dev_n} devices found.')
            #######################################################################
            # tag-related arrays
            while len(self.tag_dev) < len(self.dev_list): self.tag_dev.append({})
            while len(self.tag_chan) < len(self.dev_list): self.tag_chan.append([])
            for dev in self.dev_list:
                tags = self.tag_chan[int(sel)-1]
                n = dev[1].n_meas + dev[1].n_status + dev[1].n_state
                while len(tags) < n: tags.append({})
            #######################################################################
        elif choice == 'Select':
            if len(self.dev_list) == 0:
                return
            while True:
                self.display_menu([(f'{x[0]:<30}: {x[1].__name__:<10} => (' + ('O' if x[2] else 'X') + ')') 
                                    for x in self.dev_list])
                sel = prompt('Select a number of the device ("a/n" for all / "0" for Back): ')
                if sel.isdecimal() and 1 <= int(sel) <= len(self.dev_list):
                    self.dev_list[int(sel)-1][2] = not self.dev_list[int(sel)-1][2]
                elif sel == 'a' or sel == 'A':
                    for dev in self.dev_list: dev[2] = True
                elif sel == 'n' or sel == 'N':
                    for dev in self.dev_list: dev[2] = False
                elif sel == '0' or sel == 'Back':
                    break
                else:
                    print('Wrong choice. Try again.')
            self.sel_n = [x[2] for x in self.dev_list].count(True)
        elif choice == 'General':
            while True:
                self.display_menu([f'General tags: {self.tag_gen}',
                                   '',
                                   'Add a tag: a/A tag1=value1 tag2=value2 ...',
                                   'Remove a tag: r/R tag1 tag2 ...'],
                                   None, False)
                sel = prompt(' Add or remove a tag ("0" for Back): ').split()
                if sel[0] == 'a' or sel[0] == 'A':
                    sel.pop(0)
                    for s in sel:
                        r = re.match('(\w+)=(\w+)', s)
                        print(s, r)
                        if r is not None: self.tag_gen[r[1]] = r[2]
                        print(self.tag_gen)
                elif sel[0] == 'r' or sel[0] == 'R':
                    sel.pop(0)
                    for s in sel:
                        if s in self.tag_gen:
                            self.tag_gen.pop(s)
                elif sel[0] == '0' or sel[0] == 'Back':
                    break
                else:
                    print('Wrong choice. Try again.')
        elif choice == 'Device':
            if len(self.dev_list) == 0:
                return
            while len(self.tag_dev) < len(self.dev_list): self.tag_dev.append({})
            while True:
                self.display_menu([(f'{x[0]:<20}: {x[1].__name__:<10} => (' + ('O' if x[2] else 'X') + 
                                    f'), Tags: {self.tag_dev[idx]}') 
                                    for idx, x in enumerate(self.dev_list)])
                sel = prompt(' Add or remove a tag ("0" for Back): ').split()
                if sel[0] == 'a' or sel[0] == 'A':
                    if sel[1].isdecimal() and 1 <= int(sel[1]) <= len(self.tag_dev):
                        for s in sel[2:]:
                            r = re.match('(\w+)=(\w+)', s)
                            print(s, r)
                            if r is not None: self.tag_dev[int(sel[1])-1][r[1]] = r[2]
                elif sel[0] == 'r' or sel[0] == 'R':
                    if sel[1].isdecimal() and 1 <= int(sel[1]) <= len(self.tag_dev):
                        for s in sel[2:]:
                            if s in self.tag_dev[int(sel[1])-1]:
                                self.tag_dev[int(sel[1])-1].pop(s)
                elif sel[0] == '0' or sel[0] == 'Back':
                    break
                else:
                    print('Wrong choice. Try again.')  
        elif choice == 'Channel':
            if len(self.dev_list) == 0:
                return
            while len(self.tag_chan) < len(self.dev_list): self.tag_chan.append([])
            while True:
                self.display_menu([(f'{x[0]:<20}: {x[1].__name__:<10} => (' + ('O' if x[2] else 'X') + 
                                    f')') 
                                    for x in self.dev_list])
                sel = prompt(' Select a device ("0" for Back): ')
                if sel.isdecimal() and 1 <= int(sel) <= len(self.dev_list):
                    dev = self.dev_list[int(sel)-1]
                    tags = self.tag_chan[int(sel)-1]
                    n = dev[1].n_meas + dev[1].n_status + dev[1].n_state
                    while len(tags) < n: tags.append({})
                    while True:
                        #################################################################################
                        # make a menu
                        menus = [f'{dev[0]:<20}: {dev[1].__name__:<10} => (' + ('O' if dev[2] else 'X') + f')']
                        for i in range(dev[1].n_meas):   menus.append(f'Measure {i+1} Tag: {tags[i]}')
                        for i in range(dev[1].n_status): menus.append(f'Status  {i+1} Tag: {tags[dev[1].n_meas+i]}')
                        for i in range(dev[1].n_state):  menus.append(f'State   {i+1} Tag: {tags[dev[1].n_meas+dev[1].n_status+i]}')         
                        #################################################################################                   
                        self.display_menu(menus, None, True, True)
                        sel = prompt(' Add or remove a tag ("0" for Back): ').split()
                        if sel[0] == 'a' or sel[0] == 'A':
                            if sel[1].isdecimal() and 1 <= int(sel[1]) <= len(tags):
                                for s in sel[2:]:
                                    r = re.match('(\w+)=(\w+)', s)
                                    print(s, r)
                                    if r is not None: tags[int(sel[1])-1][r[1]] = r[2]
                        elif sel[0] == 'r' or sel[0] == 'R':
                            if sel[1].isdecimal() and 1 <= int(sel[1]) <= len(tags):
                                for s in sel[2:]:
                                    if s in tags[int(sel[1])-1]:
                                        tags[int(sel[1])-1].pop(s)
                        elif sel[0] == '0' or sel[0] == 'Back':
                            break
                        else:
                            print('Wrong choice. Try again.')  
                        #self.dev_list[int(sel)-1][2] = not self.dev_list[int(sel)-1][2]
                elif sel == '0' or sel == 'Back':
                    break
                else:
                    print('Wrong choice. Try again.')        
        elif choice == 'Frequency':
            self.freq = float(prompt('Input a update period: ', validator=float_validator))
        elif choice == 'Start':
            if self.job.is_alive():
                print(' Sender is running.')
            else:
                if self.sel_n == 0: 
                    print('No selcted devices.')
                    return
                self.sender.set_influx_setting(self.influx_url, self.influx_token, self.influx_org, self.influx_bucket)
                self.sender.set_device_setting(self.freq, self.dev_list, self.tag_gen, self.tag_dev, self.tag_chan)

                self.job = threading.Thread(target=self.sender.write_influx)
                self.job.start()
                self.status = 1
                self.update_submenu_info()
                print(' Sender turns to be running.')
        elif choice == 'Stop':
            if self.job.is_alive():
                self.sender.running = False
                self.job.join()
                self.status = 0
                self.update_submenu_info()
                print(' Sender turns to be idle.')
            else:
                print(' Sender is idle.')
                self.status = 0
                self.update_submenu_info()
        else:
            pass
        self.update_submenu_info()

    def main(self):
        while True:
            self.display_menu(self.main_menu_items)
            try:
                choice = self.session.prompt('Select a menu (number or item): ', completer=self.main_menu_completer, validator=None)
                choice = self.handle_option(self.main_menu_items, choice)

                if choice == 'Exit':
                    break
                elif choice in self.submenu_options:
                    while True:
                        self.display_menu(self.submenu_options[choice], self.submenu_info[choice] )
                        sub_choice = self.session.prompt(f'Select a sub-menu of {choice} (number or item): ', 
                                                         completer=WordCompleter(self.submenu_options[choice], ignore_case=True), validator=None)
                        sub_choice = self.handle_option(self.submenu_options[choice], sub_choice)

                        if sub_choice == 'Back':
                            break
                        elif sub_choice in self.submenu_options[choice]:
                            self.execution(sub_choice)
                            #print(f'{choice}의 {sub_choice}를 선택하셨습니다.')
                        else:
                            print('Wrong choice. Try again.')
                else:
                    print('Wrong choice. Try again.')

            except KeyboardInterrupt:
                break
            except EOFError:
                break

        if self.job.is_alive(): 
            self.sender.running = False
            self.job.join()

if __name__ == '__main__':
    cmmsis = CMMSIS()
    cmmsis.main()
    #app = Application(full_screen=True)
    #app.run()
