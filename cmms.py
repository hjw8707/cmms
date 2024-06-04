from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, \
                            QVBoxLayout, QHBoxLayout, QLineEdit, QWidget, QGridLayout, \
                            QGroupBox, QComboBox, QMessageBox, QTabWidget, QCheckBox, \
                            QLCDNumber, QStatusBar

import re
import sys, inspect
import datetime as dt
from serman import SerMan
from sermeasure import UnitType, SerMeasure

from m1 import M1, M2, M3
from tpg36x import TPG36X
from ls335 import LS335
from ls218 import LS218
from tic100 import TIC100
from bcg450 import BCG450

from typing import Dict, List

update_t = 3000

class CMMS_Port(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sm = SerMan()
        self.devcl_list: List[str] = []
        self.dev_list: List[CMMS_Measure] = []
        self.initUI()
        self.timer = QTimer()
        self.timer.setInterval(update_t)
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
        self.cb_portlist.insertItems(0, self.sm.string_ports(True))          
    
    def add_dev(self):
        port = self.sm.get_port_dev(self.cb_portlist.currentIndex())
        dev_cl  = self.cb_devlist.currentText()
        name = self.le_devname.text().strip()
        if name == '': name = dev_cl + str(len(self.dev_list))
        dev_class_ = getattr(sys.modules[__name__], dev_cl, None)
        dev = dev_class_(name, port)
        self.dev_list.append(CMMS_Measure(dev, self))
        self.lo_devices.addWidget(self.dev_list[-1])
    
    def close_dev(self, meas):
        meas.close()
        self.lo_devices.removeWidget(meas)
        self.dev_list.remove(meas)
        del meas
        #print(self.parentWidget().minimumSizeHint())
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

    perc_units = [ '%', '\N{PER MILLE SIGN}', ' ']
    perc_fac =  { '%': 1, '\N{PER MILLE SIGN}': 10 , ' ': 0.01 }

    def __init__(self, type: UnitType, *args) -> None:
        super().__init__(*args)
        if   type == UnitType.Pres: self.addItems(self.pres_units)
        elif type == UnitType.Temp: self.addItems(self.temp_units)
        elif type == UnitType.Perc: self.addItems(self.perc_units)
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
        elif self.type is UnitType.Perc:
            if inpUnit not in self.perc_units: return 0
            return self.perc_fac[self.currentText()]/self.perc_fac[inpUnit]*inpVal
        return 0

class QMeasureValue(QWidget):
    def __init__(self, type: UnitType, *args):
        super().__init__(*args)
        layout = QHBoxLayout()
        self.measure = QMeasureNumber()
        self.input_unit = ''
        self.unit = QMeasureUnit(type)
        layout.addWidget(self.measure)
        layout.addWidget(self.unit)
        self.setLayout(layout)
        #self.setLineWidth(0)
        #self.lcdDigit.setSmallDecimalPoint(True)

    def setNoValue(self):
        self.measure.display('----------')

    def setInputValue(self, value: float, flagSci = True):
        convValue = self.unit.convUnit(self.input_unit,value)
        strVal = ('%.3E' if flagSci else '%.3f') % convValue
        self.measure.display(strVal)
    
    def setInputUnit(self, value: str):
        self.input_unit = value

class QState(QWidget):
    def __init__(self, name: str, *args):
        super().__init__(*args)
        layout = QHBoxLayout()
        self.name = QLabel(name)
        self.state = QLineEdit('State')
        layout.addWidget(self.name)
        layout.addWidget(self.state)
        self.setLayout(layout)
        #self.setLineWidth(0)
        #self.lcdDigit.setSmallDecimalPoint(True)

    def setState(self, stat: str):
        self.state.setText(stat)

class QStatus(QCBIndicator):
    def __init__(self, *args):
        super().__init__(*args)
    
    def setStatus(self, status: bool):
        self.setChecked(status)


class CMMS_Measure(QWidget):
    def __init__(self, dev: SerMeasure, parent: CMMS_Port, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dev = dev
        self.pare = parent
        ####################
        # logger
        now = QDateTime.currentDateTime().toString('yyMMdd_hhmmss')
        self.logger = open('log/%s_%s_%s.txt' % (self.dev.__class__.__name__, self.dev.name, now), 'w')
        ####################
        self.initUI()

    def initUI(self):
        lb_name = QLabel(self.dev.name)
        lb_name.setFixedWidth(50)
        lb_dev  = QLabel(self.dev.__class__.__name__)
        lb_dev.setFixedWidth(50)

        self.q_meas: list[QMeasureValue] = []
        for i in range(self.dev.n_meas):
            self.q_meas.append(QMeasureValue(self.dev.type[i], self))
            self.q_meas[-1].setInputUnit(self.dev.GetUnit(i))

        self.q_states: list[QState] = []
        for i in range(self.dev.n_state):
            self.q_states.append(QState(self.dev.GetStateName(i), self))

        self.q_status: list[QStatus] = []
        for i in range(self.dev.n_status):
            self.q_status.append(QStatus(self.dev.GetStatusName(i), self))

        self.cb_indic = QCBIndicator('status')
        self.cb_indic.setFixedWidth(70)

        pb_close = QPushButton('Close')
        pb_close.setFixedWidth(70)
        pb_close.clicked.connect(lambda: self.pare.close_dev(self))

        layout = QHBoxLayout()
        layout.addWidget(lb_name)
        layout.addWidget(lb_dev)
        layoutm = QVBoxLayout()
        layoutm_state  = QHBoxLayout()
        [layoutm_state.addWidget(i) for i in self.q_states]
        layoutm_status = QHBoxLayout()
        [layoutm_status.addWidget(i) for i in self.q_status]        
        layoutm_meas   = QHBoxLayout()        
        [layoutm_meas.addWidget(i) for i in self.q_meas]
        layoutm.addLayout(layoutm_state)
        layoutm.addLayout(layoutm_status)
        layoutm.addLayout(layoutm_meas)
        layout.addLayout(layoutm)
        layout.addWidget(self.cb_indic)
        layout.addWidget(pb_close)
        self.setLayout(layout)
        
        self.timeout()
        
    def timeout(self):
        if not self.dev.is_open():
            self.dev.open() 
        self.cb_indic.setChecked(self.dev.is_open())
        if self.cb_indic.isChecked():
            logstr = QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss ')
            for i, lcd in enumerate(self.q_meas):
                meas = self.dev.GetMeasure(i)
                lcd.setInputValue(meas, self.dev.type[i] != UnitType.Perc)
                logstr = logstr + ('%6.3E ' % meas)
            for i, state in enumerate(self.q_states):
                stat = self.dev.GetState(i)
                state.setState(stat)
                logstr = logstr + ('%s ' % stat)
            for i, status in enumerate(self.q_status):
                statu = self.dev.GetStatus(i)
                status.setStatus(statu)
                logstr = logstr + str(statu) + ' '
            self.logger.write(logstr + '\n')
            self.logger.flush()
        else:
            for i in self.q_meas: i.setNoValue()
        
        
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
        self.timer.start(update_t)  # update every second

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
