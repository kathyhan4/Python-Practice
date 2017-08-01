import sys
import time
import datetime
from PyQt4 import QtGui, QtCore
import requests


DEFAULT_NUMBER = 10


class Example(QtGui.QWidget):
    def __init__(self):
        super(Example, self).__init__()
        
        self.counter = Counter()
        self.connect(self.counter, QtCore.SIGNAL('counterEvent'), self.counterEvent)
        
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('QThreads Example')
        okButton = QtGui.QPushButton("OK")
        okButton.clicked.connect(self.click)
        self.textLog = QtGui.QTextEdit()
        self.number = QtGui.QSpinBox()
        self.number.setMinimum(0)
        self.number.setMaximum(DEFAULT_NUMBER)
        self.number.setValue(DEFAULT_NUMBER)
        self.number.valueChanged.connect(self.changeNumber)
        self.pbar = QtGui.QProgressBar(self)
        self.pbar.setMaximum(DEFAULT_NUMBER)
        self.bitcoin = QtGui.QCheckBox('get bitcoin price')
        self.bitcoin.setChecked(True)
        self.bitcoin.stateChanged.connect(self.bitcoinCheck)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.number)
        vbox.addWidget(okButton)
        vbox.addWidget(self.bitcoin)
        vbox.addWidget(self.pbar)
        vbox.addWidget(self.textLog)
        self.setLayout(vbox)
        
        self.timer = Timer()
        self.connect(self.timer, QtCore.SIGNAL('timerEvent'), self.timerEvent)
        self.timer.start()
        
        self.show()
        
    def click(self):
        self.log('button clicked', type='info')
        if not self.counter.running:
            self.counter.start()
        else:
            self.log('one thread is already running!', type='error')
            
    def bitcoinCheck(self, state):
        self.log('bitcoin state changed [%s]' % state, type='info')
        if state > 0:
            self.timer.getPrice = True
        else:
            self.timer.getPrice = False
            
    def changeNumber(self, number):
        self.log('new number: %s' % number, type='info')
        self.counter.number = number
        self.pbar.setMaximum(number)
            
    def counterEvent(self, event):
        self.log(event, type='ok')
        self.pbar.setValue(event['counter'] + 1)
        
    def timerEvent(self, event):
        self.log(str(event), type='bitcoin')
        
    def log(self, text, type='error'):
        if type == 'info':
            color = "#0000ff"
        elif type == 'ok':
            color = "#008000"
        elif type == 'bitcoin':
            color = "#A9A9A9"
        else:
            color = "#ff0000"
        dt = datetime.datetime.utcnow()
        fulltext = "[%s]" % dt
        fulltext += "[%s]" % text
        ans = "<span style=\" font-size:8pt; font-weight:600; color:%s;\" >" % (color)
        ans += fulltext
        ans += "</span>"
        self.textLog.append(ans)
        self.textLog.moveCursor(QtGui.QTextCursor.End)


class Counter(QtCore.QThread):
    def __init__(self):
        super(Counter, self).__init__()
        self.running = False
        self.number = DEFAULT_NUMBER
        
    def run(self):
        self.running = True
        self.count()
        self.running = False
        
    def count(self):
        for count in range(self.number):
            dataStructure = {'counter': count, 'maximum': self.number}
            self.emit(QtCore.SIGNAL('counterEvent'), dataStructure)
            time.sleep(1)


class Timer(QtCore.QThread):
    def __init__(self):
        super(Timer, self).__init__()
        self.getPrice = True
        
    def run(self):
        while True:
            if self.getPrice:
                r = requests.get('https://api.coindesk.com/v1/bpi/currentprice.json')
                self.emit(QtCore.SIGNAL('timerEvent'), r.json())
                time.sleep(5)
            else:
                time.sleep(1)
            

def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()