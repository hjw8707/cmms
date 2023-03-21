##########################################
# PyQt version check
import pkg_resources
inst_pack = pkg_resources.working_set
list_inst_pack = ["%s" % i.key for i in inst_pack]
if   'pyqt6' in list_inst_pack: 
    pyqt = 'PyQt6'
    from PyQt6 import QtGui
    from PyQt6.QtCore import Qt, QTimer, QDateTime
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, \
                                QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QGridLayout, \
                                QGroupBox, QComboBox, QMessageBox, QTabWidget, QCheckBox, \
                                QLCDNumber, QStatusBar
elif 'pyqt5' in list_inst_pack: 
    pyqt = 'PyQt5'
    from PyQt5 import QtGui
    from PyQt5.QtCore import Qt, QTimer, QDateTime
    from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, \
                                QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QGridLayout, \
                                QGroupBox, QComboBox, QMessageBox, QTabWidget, QCheckBox, \
                                QLCDNumber, QStatusBar
else:
    print("No PyQt module found.")
    exit()
##########################################

import re
import sys, inspect
import datetime as dt
from serman import SerMan
from sermeasure import SerMeasure

from m1 import M1, M2
from tpg36x import TPG36X
from ls335 import LS335
from tic100 import TIC100
from bcg450 import BCG450

from enum import Enum, auto
from typing import Dict, List

class UnitType(Enum):
    Pres = auto()
    Temp = auto()

class CMMS_Port(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sm = SerMan()
        self.devcl_list: List[str] = []
        self.dev_list: List[CMMS_Measure] = []
        self.initUI()
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.timeout)
        self.timer.start()

    def initUI(self):
        lb_portlist = QLabel("Port List")
        self.cb_portlist = QComboBox()
        pb_portlist_update = QPushButton('Update')
        pb_portlist_update.clicked.connect(self.ports_update)
        lb_devlist = QLabel("Device List")
        self.cb_devlist = QComboBox()
        self.le_devname = QLineEdit()
        pb_adddev = QPushButton('Add Device')
        pb_adddev.clicked.connect(self.add_dev)        
                
        lo_portlist = QGridLayout()
        lo_portlist.addWidget(lb_portlist, 0, 0)
        lo_portlist.addWidget(self.cb_portlist, 0, 1)
        lo_portlist.addWidget(pb_portlist_update, 0, 3)
        lo_portlist.addWidget(lb_devlist, 1, 0)
        lo_portlist.addWidget(self.cb_devlist, 1, 1)
        lo_portlist.addWidget(self.le_devname, 1, 2)
        lo_portlist.addWidget(pb_adddev, 1, 3)
        #print(lo_portlist.minimumSize())
        #print(lo_portlist.sizeHint())

        self.lo_devices = QVBoxLayout()
        
        lo_total = QVBoxLayout()
        lo_total.addLayout(lo_portlist)
        lo_total.addLayout(self.lo_devices)
        self.setLayout(lo_total)
        
        self.ports_update()
        self.dev_update()
        
    def dev_update(self):
        for name, obj in inspect.getmembers(sys.modules[__name__]):          
            if inspect.isclass(obj) and obj.__base__.__name__ == 'SerMeasure':
                self.devcl_list.append(name)        
        self.cb_devlist.clear()
        self.cb_devlist.insertItems(0, self.devcl_list)
                
    def ports_update(self):
        self.sm.load_ports()
        self.cb_portlist.clear()
        self.cb_portlist.insertItems(0, self.sm.string_ports(False))          
    
    def add_dev(self):
        port = self.sm.get_port_dev(self.cb_portlist.currentIndex())
        dev_cl  = self.cb_devlist.currentText()
        name = self.le_devname.text().strip()
        if name == '': name = dev_cl
        dev_class_ = getattr(sys.modules[__name__], dev_cl, None)
        dev = dev_class_(name, port)
        self.dev_list.append(CMMS_Measure(dev, self))
        self.lo_devices.addWidget(self.dev_list[-1])
    
    def close_dev(self, meas):
        meas.close()
        self.lo_devices.removeWidget(meas)
        self.dev_list.remove(meas)
        del meas
        print(self.parentWidget().minimumSizeHint())
        self.parentWidget().adjustSize()
        
    def timeout(self):
        for x in [e.timeout for e in self.dev_list]: x()

class QCBIndicator(QCheckBox):
    def __init__(self, *args):
        super().__init__(*args)
        self.setDisabled(True)
        self.setStyleSheet("QCheckBox::indicator:disabled:checked""{"
                           "width :10px;""height :10px;"
                           "background-color : green;" "}"
                           "QCheckBox::indicator:disabled:unchecked""{"
                           "width :10px;" "height :10px;"
                           "background-color : red;" "}"
                           "QCheckBox" "{" "color: black;" "}")

class QMeasureNumber(QLCDNumber):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.setDigitCount(10)
        self.setMinimumWidth(150)
        self.setMinimumHeight(30)
        

class QMeasureUnit(QComboBox):
    pres_units = [ 'Torr', 'Pa', 'atm', 'psi' ]
    pres_fac =  { 'Pa': 1, 'Torr': 0.00750064 , 'atm': 9.86923e-06, 'psi': 0.000145038 }

    temp_units = [ 'K', '\N{DEGREE SIGN}C', '\N{DEGREE SIGN}F' ]

    def __init__(self, type: UnitType, *args) -> None:
        super().__init__(*args)
        if   type == UnitType.Pres: self.addItems(self.pres_units)
        elif type == UnitType.Temp: self.addItems(self.temp_units)
        self.type = type
        self.setCurrentIndex(0)
        
    def convUnit(self, inpUnit: str, inpVal: float):
        if self.type is UnitType.Pres:
            if inpUnit not in self.pres_units: return 0
            return self.pres_fac[self.currentText()]/self.pres_fac[inpUnit]*inpVal
        elif self.type is UnitType.Temp:
            if inpUnit not in self.temp_units: return 0
            if inpUnit == 'K':
                if self.currentText() == 'K':                return inpVal
                if self.currentText() == '\N{DEGREE SIGN}C': return inpVal - 273.15
                if self.currentText() == '\N{DEGREE SIGN}F': return (inpVal - 273.15)*9/5+32
            if inpUnit == '\N{DEGREE SIGN}C': 
                if self.currentText() == 'K':                return inpVal + 273.15
                if self.currentText() == '\N{DEGREE SIGN}C': return inpVal
                if self.currentText() == '\N{DEGREE SIGN}F': return inpVal*9/5+32
            if inpUnit == '\N{DEGREE SIGN}F':
                if self.currentText() == 'K':                return (inpVal - 32)*5/9 + 273.15
                if self.currentText() == '\N{DEGREE SIGN}C': return (inpVal - 32)*5/9
                if self.currentText() == '\N{DEGREE SIGN}F': return inpVal
        return 0

class QMeasureValue(QWidget):
    def __init__(self, *args):
        super().__init__(*args)
        layout = QHBoxLayout()
        self.measure = QMeasureNumber()
        self.input_unit = ''
        self.unit = QMeasureUnit(UnitType.Pres)
        layout.addWidget(self.measure)
        layout.addWidget(self.unit)
        self.setLayout(layout)
        #self.setLineWidth(0)
        #self.lcdDigit.setSmallDecimalPoint(True)

    def setNoValue(self):
        self.measure.display('----------')

    def setInputValue(self, value: float):
        strVal = '%.3E' % self.unit.convUnit(self.input_unit,value)
        self.measure.display(strVal)
    
    def setInputUnit(self, value: str):
        self.input_unit = value

class CMMS_Measure(QWidget):
    def __init__(self, dev: SerMeasure, parent: CMMS_Port, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dev = dev
        self.parent = parent
        self.initUI()

            
    def initUI(self):
        lb_name = QLabel(self.dev.name)
        lb_name.setFixedWidth(50)
        lb_dev  = QLabel(self.dev.__class__.__name__)
        lb_dev.setFixedWidth(50)
        self.lcd_meas: list[QMeasureValue] = []
        for i in range(self.dev.n_meas):
            self.lcd_meas.append(QMeasureValue(self))
            self.lcd_meas[-1].setInputUnit(self.dev.GetUnit(i))
        self.cb_indic = QCBIndicator('status')
        self.cb_indic.setFixedWidth(70)
        pb_close = QPushButton('Close')
        pb_close.setFixedWidth(70)
        pb_close.clicked.connect(lambda: self.parent.close_dev(self))

        layout = QHBoxLayout()
        layout.addWidget(lb_name)
        layout.addWidget(lb_dev)
        [layout.addWidget(i) for i in self.lcd_meas]
        layout.addWidget(self.cb_indic)
        layout.addWidget(pb_close)
        self.setLayout(layout)
        
        self.timeout()
        
    def timeout(self):
        if not self.dev.is_open():
            self.dev.open() 
        self.cb_indic.setChecked(self.dev.is_open())
        if self.cb_indic.isChecked():
            for i, lcd in enumerate(self.lcd_meas): 
                lcd.setInputValue(self.dev.GetMeasure(i))
        else:
            for i in self.lcd_meas: i.setNoValue()
        
        
class CMMS_GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("CMMS: CENS Measurement Management System")
        self.setCentralWidget(CMMS_Port())
        self.addStatusBar()

    def addStatusBar(self):
        statusBar = QStatusBar()
        self.setStatusBar(statusBar)
        self.timeLabel = QLabel(QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss '))
        statusBar.addPermanentWidget(self.timeLabel)
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateStatusBar)
        self.timer.start(1000)  # update every second

        #print(self.centralWidget().minimumSizeHint())
        self.setMinimumSize(self.centralWidget().minimumSizeHint())
        self.adjustSize()
        self.show()

    def updateStatusBar(self):
        self.timeLabel.setText(QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss'))


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = CMMS_GUI()
    window.show()
    sys.exit(app.exec())        
