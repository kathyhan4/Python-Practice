# -*- coding: utf-8 -*-
"""
Created on Sat Jul 22 16:01:15 2017

@author: cleroy
"""

from PyQt4 import QtGui
import sys


parameters = {'powerSupply': {'type': 'value', 'value': 1, 'label': 'Power Supply',
                              'min': 0, 'max': 10},
              'powerSupply1': {'type': 'value', 'value': 0, 'label': 'NOT CONNECTED - 1',
                               'min': 0, 'max': 10},
              'randomText': {'type': 'text', 'label': 'Something', 'text': 'hello'}}


class ParameterTemplate(QtGui.QWidget):
    def __init__(self, name):
        super(ParameterTemplate, self).__init__()
        self.name = name
        data = parameters[self.name]
        
        hbox = QtGui.QHBoxLayout()
        
        self.label = QtGui.QLabel(data['label'])
        hbox.addWidget(self.label)
        
        if data['type'] == 'value':
            self.value = QtGui.QSpinBox()
            self.value.setMinimum(data['min'])
            self.value.setMaximum(data['max'])
            self.value.valueChanged.connect(self.valueChanged)
            self.value.setValue(data['value'])
            hbox.addWidget(self.value)
        elif data['type'] == 'text':
            self.line = QtGui.QLineEdit()
            self.line.textChanged.connect(self.textChanged)
            self.line.setText(data['text'])
            hbox.addWidget(self.line)
        
        self.setLayout(hbox)
        
    def valueChanged(self, value):
        parameters[self.name]['value'] = value
        print parameters
        
    def textChanged(self, text):
        parameters[self.name]['text'] = text
        print parameters


class Example(QtGui.QWidget):
    def __init__(self):
        super(Example, self).__init__()
        
        self.parametersUIFactory()
        
        self.show()
        
    def parametersUIFactory(self):
        vbox = QtGui.QVBoxLayout()
        for param in parameters:
            print param
            widget = ParameterTemplate(param)
            vbox.addWidget(widget)
        self.setLayout(vbox)


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()