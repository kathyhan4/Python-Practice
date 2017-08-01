# -------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      khan
#
# Created:     25/07/2017
# Copyright:   (c) khan 2017
# Licence:     <your licence>
# -------------------------------------------------------------------------------

import sys, time
from PyQt4 import QtCore, QtGui
import sys, os
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QThread
from PyQt4.QtGui import *
import threading
import serial
import numpy as np
import time
from serial.tools import list_ports
import TDKLambdaDriver_1_0 as TDK
import datetime
import csv

CCCabinetPythonControlsVersion = str(1.6)
first_time_seconds = str('%.0f' % round(time.time(), 1))
## Version change notes
# Ver 1.0 is basically functional python code
# list inputs and outputs
# all fans set to same set temp, 8 fans controlled individually, each by two temp sensors

# v1.2 now displays time into cycle
# v1.3 includes smoke sensor lockout that tells arduino to turn pin 14 high, killing TDK output permanently upon smoke signal
# v1.4 uses only one timer in a (hopefully not vain) attempt to solve python.exe from crashing
# v1.5 was a complete flop
# v1.6 implements QThread to give background processes their own thread to not crash the GUI

# Global Definitions
TMRONESECOND_INTERVAL = 2  # seconds between communication with Arduino
SAVETIME = 10  # save every 10 seconds, make this divisible by TMRONESECOND_INTERVAL
DEFAULT_BIAS_CURRENT = "0"
DEFAULT_BIAS_ON_TIME = "7"
DEFAULT_BIAS_OFF_TIME = "5"
DEFAULT_OVERTEMP_SETPOINT = "100"
DEFAULT_CURRENT_ON_SETPOINT = "85"
DEFAULT_CURRENT_OFF_SETPOINT = "25"
BAUDRATE = "57600"
BIAS_CURRENT_STATUS_INITIAL = 0
INTERLOCK = 0
VOLTAGE_COMPLIANCE = "60"
VERBOSE = 1  # Set to 1 to enable debug print, set to 0 to disable debug print

dict_to_Arduino = {"key1": 1,
                   "key2": 2,
                   "key3": 3, }

dict_to_TDK = {"key1": 1,
               "key2": 2,
               "key3": 3, }

dict_to_GUI = {
    "PowerSupplies": [
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, },
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, },
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, },
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, },
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, },
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, },
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, },
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, },
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, },
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, },
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, },
        {"isConnected": "Not Connected", "Current": 0.0, "Voltage": 0.0, }, ],
    "Temperatures": [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ],
    "FanSpeeds": [
        0, 0, 0, 0, 0, 0, 0, 0, ],
    "CycleNumber": 0,
    "MinutesIntoCycle": 0,
    "CurrentBiasStatus": 'Off'}


class Window(QtGui.QWidget):
    # ================BEGINNING OF FORM INIT FUNCTIONS===========================
    # TDK power supplies in Gen language, USB setting for master power supply, ADR 1, RS485 setting for others (2-31 optional, probably use 2-12), baudrate 57600

    # This function fires just once, upon startup. Usually used to define the overall shape of the window, title, etc.
    def __init__(self):
        super(Window, self).__init__()
        self.setup()
        self.setWindowTitle("Current Cycling Controls " + str(CCCabinetPythonControlsVersion))
        self.initUI()

    # This function fires once - use this to init variables4
    def setup(self):
        self.TDK = TDK

    def WriteToFile(self, message, OutputFile, first_time_seconds):
        file = open(OutputFile + first_time_seconds + '.txt', 'a')
        file.write(message)
        file.close()
        # here OutputFile is self.txtSaveFilePathName.text(), first_time_seconds is first_time_seconds

    # ======================END OF FORM INIT FUNCTIONS==========================

    # ==============BEGINNING OF USER INTERFACE FUNCTIONS=======================
    # This function also fires once (it's fired by the last line in the __init__ function. This function is typically used to define buttons, textboxes, etc.
    def initUI(self):
        self.threadPool = []
        self.counter = 0
        # Defines colors
        self.palette_red = QtGui.QPalette()
        self.palette_red.setColor(QtGui.QPalette.Foreground, QtCore.Qt.red)
        self.palette_green = QtGui.QPalette()
        self.palette_green.setColor(QtGui.QPalette.Foreground, QtCore.Qt.green)

        # Cycle Number
        self.lblCycleNumberLabel = QtGui.QLabel("Cycle #: ", self)
        self.lblCycleNumberLabel.move(230, 0)
        self.lblCycleNumberLabel.resize(100, 30)

        # Cycle Number
        self.lblCycleNumber = QtGui.QLabel("1", self)
        self.lblCycleNumber.move(300, 0)
        self.lblCycleNumber.resize(130, 30)

        # bias state
        self.lblBiasStateLabel = QtGui.QLabel("Bias State: ", self)
        self.lblBiasStateLabel.move(330, 0)
        self.lblBiasStateLabel.resize(100, 30)

        # bias state
        self.lblBiasState = QtGui.QLabel("0", self)
        self.lblBiasState.move(400, 0)
        self.lblBiasState.resize(130, 30)

        # Cycle Time
        self.lblCycleTimeLabel = QtGui.QLabel("Minutes into Cycle: ", self)
        self.lblCycleTimeLabel.move(180, 15)
        self.lblCycleTimeLabel.resize(150, 30)

        # Cycle Time
        self.lblCycleTime = QtGui.QLabel("0", self)
        self.lblCycleTime.move(300, 15)
        self.lblCycleTime.resize(130, 30)

        # User name
        self.lblUser = QtGui.QLabel("Operator: ", self)
        self.lblUser.move(25, 400)
        self.lblUser.resize(150, 45)

        # User name input
        self.txtUserName = QtGui.QLineEdit(self)
        self.txtUserName.setText('Operator')
        self.txtUserName.move(150, 400)
        self.txtUserName.resize(100, 30)

        # Save file location and name
        self.lblSaveFileLabel = QtGui.QLabel("Save Path and Name: ", self)
        self.lblSaveFileLabel.move(25, 450)
        self.lblSaveFileLabel.resize(150, 45)

        # Bias current textbox 6
        self.txtSaveFilePathName = QtGui.QLineEdit(self)
        self.txtSaveFilePathName.setText("Y:\\Current Cycling\\Kat's Data\\Data\\CCData_")
        self.txtSaveFilePathName.move(150, 450)
        self.txtSaveFilePathName.resize(400, 30)

        # Reconnect push button
        self.btnReconnect = QtGui.QPushButton("Reconnect", self)
        self.btnReconnect.clicked.connect(self.btnReconnectClicked)
        self.btnReconnect.resize(150, 50)
        self.btnReconnect.move(10, 10)

        # Arduino firmware version label
        self.lblArduinoFWVersion = QtGui.QLabel("Arduino firmware version: ", self)
        self.lblArduinoFWVersion.move(10, 60)
        self.lblArduinoFWVersion.resize(150, 30)

        # TDK interlock active?
        self.chkTDKInterlockActive = QtGui.QCheckBox('TDK Interlock Active', self)
        self.chkTDKInterlockActive.setChecked(True)
        self.chkTDKInterlockActive.resize(300, 30)
        self.chkTDKInterlockActive.move(600, 450)

        ##        #Bias current label
        ##        self.lblBiasCurrent = QtGui.QLabel("Bias Current: ", self)
        ##        self.lblBiasCurrent.move(200,10)
        ##        self.lblBiasCurrent.resize(150,30)
        ##        self.lblBiasCurrentUnit = QtGui.QLabel("A", self)
        ##        self.lblBiasCurrentUnit.move(305,10)
        ##        self.lblBiasCurrentUnit.resize(50,30)

        # Bias time on label
        self.lblBiasOnTime = QtGui.QLabel("Bias On Time: ", self)
        self.lblBiasOnTime.move(200, 40)
        self.lblBiasOnTime.resize(150, 30)
        self.lblBiasOnTimeUnit = QtGui.QLabel("min", self)
        self.lblBiasOnTimeUnit.move(305, 40)
        self.lblBiasOnTimeUnit.resize(50, 30)

        # Bias time off label
        self.lblBiasOffTime = QtGui.QLabel("Bias Off Time: ", self)
        self.lblBiasOffTime.move(200, 70)
        self.lblBiasOffTime.resize(150, 30)
        self.lblBiasOffTimeUnit = QtGui.QLabel("min", self)
        self.lblBiasOffTimeUnit.move(305, 70)
        self.lblBiasOffTimeUnit.resize(50, 30)

        ##        #Bias current textbox
        ##        self.txtBiasCurrent = QtGui.QLineEdit(self)
        ##        self.txtBiasCurrent.setText(DEFAULT_BIAS_CURRENT)
        ##        self.txtBiasCurrent.move(270, 12)
        ##        self.txtBiasCurrent.resize(30, 25)

        # Bias on time textbox
        self.txtBiasOnTime = QtGui.QLineEdit(self)
        self.txtBiasOnTime.setText(DEFAULT_BIAS_ON_TIME)
        self.txtBiasOnTime.move(270, 42)
        self.txtBiasOnTime.resize(30, 25)

        # Bias off time textbox
        self.txtBiasOffTime = QtGui.QLineEdit(self)
        self.txtBiasOffTime.setText(DEFAULT_BIAS_OFF_TIME)
        self.txtBiasOffTime.move(270, 72)
        self.txtBiasOffTime.resize(30, 25)

        # Current on temperature setpoint label
        self.lblCurrentOnTempSetpoint = QtGui.QLabel("Current on temperature set point: ", self)
        self.lblCurrentOnTempSetpoint.move(350, 10)
        self.lblCurrentOnTempSetpoint.resize(200, 30)
        self.lblCurrentOnTempSetpointUnit = QtGui.QLabel("deg. C", self)
        self.lblCurrentOnTempSetpointUnit.move(570, 10)
        self.lblCurrentOnTempSetpointUnit.resize(50, 30)

        # Current on temperature setpoint textbox
        self.txtCurrentOnTempSetpoint = QtGui.QLineEdit(self)
        self.txtCurrentOnTempSetpoint.setText(DEFAULT_CURRENT_ON_SETPOINT)
        self.txtCurrentOnTempSetpoint.move(535, 12)
        self.txtCurrentOnTempSetpoint.resize(30, 25)

        # Current off temperature setpoint label
        self.lblCurrentOffTempSetpoint = QtGui.QLabel("Current off temperature set point: ", self)
        self.lblCurrentOffTempSetpoint.move(350, 40)
        self.lblCurrentOffTempSetpoint.resize(200, 30)
        self.lblCurrentOffTempSetpointUnit = QtGui.QLabel("deg. C", self)
        self.lblCurrentOffTempSetpointUnit.move(570, 40)
        self.lblCurrentOffTempSetpointUnit.resize(50, 30)

        # Current off temperature setpoint textbox
        self.txtCurrentOffTempSetpoint = QtGui.QLineEdit(self)
        self.txtCurrentOffTempSetpoint.setText(DEFAULT_CURRENT_OFF_SETPOINT)
        self.txtCurrentOffTempSetpoint.move(535, 42)
        self.txtCurrentOffTempSetpoint.resize(30, 25)

        # Overtemp setpoint label
        self.lblOvertempSetpoint = QtGui.QLabel("Over-temperature set point: ", self)
        self.lblOvertempSetpoint.move(350, 70)
        self.lblOvertempSetpoint.resize(200, 30)
        self.lblOvertempSetpointUnit = QtGui.QLabel("deg. C", self)
        self.lblOvertempSetpointUnit.move(570, 70)
        self.lblOvertempSetpointUnit.resize(50, 30)

        # Overtemp setpoint textbox
        self.txtOvertempSetpoint = QtGui.QLineEdit(self)
        self.txtOvertempSetpoint.setText(DEFAULT_OVERTEMP_SETPOINT)
        self.txtOvertempSetpoint.move(535, 72)
        self.txtOvertempSetpoint.resize(30, 25)

        # Start push button
        self.btnStart = QtGui.QPushButton("Start", self)
        self.btnStart.clicked.connect(self.btnStartClicked)
        self.btnStart.resize(100, 45)
        self.btnStart.move(630, 10)

        # Stop push button
        self.btnStop = QtGui.QPushButton("Stop", self)
        self.btnStop.clicked.connect(self.btnStopClicked)
        self.btnStop.resize(100, 40)
        self.btnStop.move(630, 60)

        # Exit push button
        self.btnExit = QtGui.QPushButton("Exit", self)
        self.btnExit.clicked.connect(self.btnExitClicked)
        self.btnExit.resize(100, 40)
        self.btnExit.move(745, 60)

        # Power supply label
        self.lblPowerSupplyLabel = QtGui.QLabel("Power Supply: ", self)
        self.lblPowerSupplyLabel.move(10, 100)
        self.lblPowerSupplyLabel.resize(100, 30)

        # Power supply 1
        self.lblPowerSupply1 = QtGui.QLabel("NOT CONNECTED - 1 ", self)
        self.lblPowerSupply1.move(10, 100 + 1 * 20)
        self.lblPowerSupply1.resize(130, 30)

        # Power supply 2
        self.lblPowerSupply2 = QtGui.QLabel("NOT CONNECTED - 2 ", self)
        self.lblPowerSupply2.move(10, 100 + 2 * 20)
        self.lblPowerSupply2.resize(130, 30)

        # Power supply 3
        self.lblPowerSupply3 = QtGui.QLabel("NOT CONNECTED - 3 ", self)
        self.lblPowerSupply3.move(10, 100 + 3 * 20)
        self.lblPowerSupply3.resize(130, 30)

        # Power supply 4
        self.lblPowerSupply4 = QtGui.QLabel("NOT CONNECTED - 4", self)
        self.lblPowerSupply4.move(10, 100 + 4 * 20)
        self.lblPowerSupply4.resize(130, 30)

        # Power supply 5
        self.lblPowerSupply5 = QtGui.QLabel("NOT CONNECTED - 5", self)
        self.lblPowerSupply5.move(10, 100 + 5 * 20)
        self.lblPowerSupply5.resize(130, 30)

        # Power supply 6
        self.lblPowerSupply6 = QtGui.QLabel("NOT CONNECTED - 6", self)
        self.lblPowerSupply6.move(10, 100 + 6 * 20)
        self.lblPowerSupply6.resize(130, 30)

        # Power supply 7
        self.lblPowerSupply7 = QtGui.QLabel("NOT CONNECTED - 7", self)
        self.lblPowerSupply7.move(10, 100 + 7 * 20)
        self.lblPowerSupply7.resize(130, 30)

        # Power supply 8
        self.lblPowerSupply8 = QtGui.QLabel("NOT CONNECTED - 8", self)
        self.lblPowerSupply8.move(10, 100 + 8 * 20)
        self.lblPowerSupply8.resize(130, 30)

        # Power supply 9
        self.lblPowerSupply9 = QtGui.QLabel("NOT CONNECTED - 9", self)
        self.lblPowerSupply9.move(10, 100 + 9 * 20)
        self.lblPowerSupply9.resize(130, 30)

        # Power supply 10
        self.lblPowerSupply10 = QtGui.QLabel("NOT CONNECTED - 10", self)
        self.lblPowerSupply10.move(10, 100 + 10 * 20)
        self.lblPowerSupply10.resize(130, 30)

        # Power supply 11
        self.lblPowerSupply11 = QtGui.QLabel("NOT CONNECTED - 11", self)
        self.lblPowerSupply11.move(10, 100 + 11 * 20)
        self.lblPowerSupply11.resize(130, 30)

        # Power supply 12
        self.lblPowerSupply12 = QtGui.QLabel("NOT CONNECTED - 12", self)
        self.lblPowerSupply12.move(10, 100 + 12 * 20)
        self.lblPowerSupply12.resize(130, 30)

        # Current label
        self.lblCurrentLabel = QtGui.QLabel("Current (A): ", self)
        self.lblCurrentLabel.move(140, 100)
        self.lblCurrentLabel.resize(100, 30)

        # Current from power supply - 1
        self.lblCurrent1 = QtGui.QLabel("0.0A", self)
        self.lblCurrent1.move(140, 100 + 1 * 20)
        self.lblCurrent1.resize(130, 30)

        # Current from power supply - 2
        self.lblCurrent2 = QtGui.QLabel("0.0A", self)
        self.lblCurrent2.move(140, 100 + 2 * 20)
        self.lblCurrent2.resize(130, 30)

        # Current from power supply - 3
        self.lblCurrent3 = QtGui.QLabel("0.0A", self)
        self.lblCurrent3.move(140, 100 + 3 * 20)
        self.lblCurrent3.resize(130, 30)

        # Current from power supply - 4
        self.lblCurrent4 = QtGui.QLabel("0.0A", self)
        self.lblCurrent4.move(140, 100 + 4 * 20)
        self.lblCurrent4.resize(130, 30)

        # Current from power supply - 5
        self.lblCurrent5 = QtGui.QLabel("0.0A", self)
        self.lblCurrent5.move(140, 100 + 5 * 20)
        self.lblCurrent5.resize(130, 30)

        # Current from power supply - 6
        self.lblCurrent6 = QtGui.QLabel("0.0A", self)
        self.lblCurrent6.move(140, 100 + 6 * 20)
        self.lblCurrent6.resize(130, 30)

        # Current from power supply - 7
        self.lblCurrent7 = QtGui.QLabel("0.0A", self)
        self.lblCurrent7.move(140, 100 + 7 * 20)
        self.lblCurrent7.resize(130, 30)

        # Current from power supply - 8
        self.lblCurrent8 = QtGui.QLabel("0.0A", self)
        self.lblCurrent8.move(140, 100 + 8 * 20)
        self.lblCurrent8.resize(130, 30)

        # Current from power supply - 9
        self.lblCurrent9 = QtGui.QLabel("0.0A", self)
        self.lblCurrent9.move(140, 100 + 9 * 20)
        self.lblCurrent9.resize(130, 30)

        # Current from power supply - 10
        self.lblCurrent10 = QtGui.QLabel("0.0A", self)
        self.lblCurrent10.move(140, 100 + 10 * 20)
        self.lblCurrent10.resize(130, 30)

        # Current from power supply - 11
        self.lblCurrent11 = QtGui.QLabel("0.0A", self)
        self.lblCurrent11.move(140, 100 + 11 * 20)
        self.lblCurrent11.resize(130, 30)

        # Current from power supply - 12
        self.lblCurrent12 = QtGui.QLabel("0.0A", self)
        self.lblCurrent12.move(140, 100 + 12 * 20)
        self.lblCurrent12.resize(130, 30)

        # Voltage label
        self.lblVoltageLabel = QtGui.QLabel("Voltage (V): ", self)
        self.lblVoltageLabel.move(235, 100)
        self.lblVoltageLabel.resize(100, 30)

        # Voltage from power supply - 1
        self.lblVoltage1 = QtGui.QLabel("0.0V", self)
        self.lblVoltage1.move(235, 100 + 1 * 20)
        self.lblVoltage1.resize(130, 30)

        # Voltage from power supply - 2
        self.lblVoltage2 = QtGui.QLabel("0.0V", self)
        self.lblVoltage2.move(235, 100 + 2 * 20)
        self.lblVoltage2.resize(130, 30)

        # Voltage from power supply - 3
        self.lblVoltage3 = QtGui.QLabel("0.0V", self)
        self.lblVoltage3.move(235, 100 + 3 * 20)
        self.lblVoltage3.resize(130, 30)

        # Voltage from power supply - 4
        self.lblVoltage4 = QtGui.QLabel("0.0V", self)
        self.lblVoltage4.move(235, 100 + 4 * 20)
        self.lblVoltage4.resize(130, 30)

        # Voltage from power supply - 5
        self.lblVoltage5 = QtGui.QLabel("0.0V", self)
        self.lblVoltage5.move(235, 100 + 5 * 20)
        self.lblVoltage5.resize(130, 30)

        # Voltage from power supply - 6
        self.lblVoltage6 = QtGui.QLabel("0.0V", self)
        self.lblVoltage6.move(235, 100 + 6 * 20)
        self.lblVoltage6.resize(130, 30)

        # Voltage from power supply - 7
        self.lblVoltage7 = QtGui.QLabel("0.0V", self)
        self.lblVoltage7.move(235, 100 + 7 * 20)
        self.lblVoltage7.resize(130, 30)

        # Voltage from power supply - 8
        self.lblVoltage8 = QtGui.QLabel("0.0V", self)
        self.lblVoltage8.move(235, 100 + 8 * 20)
        self.lblVoltage8.resize(130, 30)

        # Voltage from power supply - 9
        self.lblVoltage9 = QtGui.QLabel("0.0V", self)
        self.lblVoltage9.move(235, 100 + 9 * 20)
        self.lblVoltage9.resize(130, 30)

        # Voltage from power supply - 10
        self.lblVoltage10 = QtGui.QLabel("0.0V", self)
        self.lblVoltage10.move(235, 100 + 10 * 20)
        self.lblVoltage10.resize(130, 30)

        # Voltage from power supply - 11
        self.lblVoltage11 = QtGui.QLabel("0.0V", self)
        self.lblVoltage11.move(235, 100 + 11 * 20)
        self.lblVoltage11.resize(130, 30)

        # Voltage from power supply - 12
        self.lblVoltage12 = QtGui.QLabel("0.0V", self)
        self.lblVoltage12.move(235, 100 + 12 * 20)
        self.lblVoltage12.resize(130, 30)

        # Thermistor label
        self.lblThermistorLabel = QtGui.QLabel("Thermistor Temp (C): ", self)
        self.lblThermistorLabel.move(310, 100)
        self.lblThermistorLabel.resize(120, 30)

        # Thermistor 1
        self.lblThermistor1 = QtGui.QLabel("1: ", self)
        self.lblThermistor1.move(310, 100 + 1 * 20)
        self.lblThermistor1.resize(100, 30)

        # Thermistor Value 1
        self.lblThermistorValue1 = QtGui.QLabel("0", self)
        self.lblThermistorValue1.move(340, 100 + 1 * 20)
        self.lblThermistorValue1.resize(100, 30)

        # Thermistor 2
        self.lblThermistor2 = QtGui.QLabel("2: ", self)
        self.lblThermistor2.move(310, 100 + 2 * 20)
        self.lblThermistor2.resize(100, 30)

        # Thermistor Value 2
        self.lblThermistorValue2 = QtGui.QLabel("0", self)
        self.lblThermistorValue2.move(340, 100 + 2 * 20)
        self.lblThermistorValue2.resize(100, 30)

        # Thermistor 3
        self.lblThermistor3 = QtGui.QLabel("3: ", self)
        self.lblThermistor3.move(410, 100 + 1 * 20)
        self.lblThermistor3.resize(100, 30)

        # Thermistor Value 3
        self.lblThermistorValue3 = QtGui.QLabel("0", self)
        self.lblThermistorValue3.move(440, 100 + 1 * 20)
        self.lblThermistorValue3.resize(100, 30)

        # Thermistor 4
        self.lblThermistor4 = QtGui.QLabel("4: ", self)
        self.lblThermistor4.move(410, 100 + 2 * 20)
        self.lblThermistor4.resize(100, 30)

        # Thermistor Value 4
        self.lblThermistorValue4 = QtGui.QLabel("0", self)
        self.lblThermistorValue4.move(440, 100 + 2 * 20)
        self.lblThermistorValue4.resize(100, 30)

        # Thermistor 5
        self.lblThermistor5 = QtGui.QLabel("5: ", self)
        self.lblThermistor5.move(310, 100 + 4 * 20)
        self.lblThermistor5.resize(100, 30)

        # Thermistor Value 5
        self.lblThermistorValue5 = QtGui.QLabel("0", self)
        self.lblThermistorValue5.move(340, 100 + 4 * 20)
        self.lblThermistorValue5.resize(100, 30)

        # Thermistor 6 new
        self.lblThermistor6 = QtGui.QLabel("6: ", self)
        self.lblThermistor6.move(310, 100 + 5 * 20)
        self.lblThermistor6.resize(100, 30)

        # Thermistor Value 6
        self.lblThermistorValue6 = QtGui.QLabel("0", self)
        self.lblThermistorValue6.move(340, 100 + 5 * 20)
        self.lblThermistorValue6.resize(100, 30)

        # Thermistor 7
        self.lblThermistor7 = QtGui.QLabel("7: ", self)
        self.lblThermistor7.move(410, 100 + 4 * 20)
        self.lblThermistor7.resize(100, 30)

        # Thermistor Value 7
        self.lblThermistorValue7 = QtGui.QLabel("0", self)
        self.lblThermistorValue7.move(440, 100 + 4 * 20)
        self.lblThermistorValue7.resize(100, 30)

        # Thermistor 8
        self.lblThermistor8 = QtGui.QLabel("8: ", self)
        self.lblThermistor8.move(410, 100 + 5 * 20)
        self.lblThermistor8.resize(100, 30)

        # Thermistor Value 8
        self.lblThermistorValue8 = QtGui.QLabel("0", self)
        self.lblThermistorValue8.move(440, 100 + 5 * 20)
        self.lblThermistorValue8.resize(100, 30)

        # Thermistor 9
        self.lblThermistor9 = QtGui.QLabel("9: ", self)
        self.lblThermistor9.move(310, 100 + 7 * 20)
        self.lblThermistor9.resize(100, 30)

        # Thermistor Value 9
        self.lblThermistorValue9 = QtGui.QLabel("0", self)
        self.lblThermistorValue9.move(340, 100 + 7 * 20)
        self.lblThermistorValue9.resize(100, 30)

        # Thermistor 10
        self.lblThermistor10 = QtGui.QLabel("10: ", self)
        self.lblThermistor10.move(310, 100 + 8 * 20)
        self.lblThermistor10.resize(100, 30)

        # Thermistor Value 10
        self.lblThermistorValue10 = QtGui.QLabel("0", self)
        self.lblThermistorValue10.move(340, 100 + 8 * 20)
        self.lblThermistorValue10.resize(100, 30)

        # Thermistor 11
        self.lblThermistor11 = QtGui.QLabel("11: ", self)
        self.lblThermistor11.move(410, 100 + 7 * 20)
        self.lblThermistor11.resize(100, 30)

        # Thermistor Value 11
        self.lblThermistorValue11 = QtGui.QLabel("0", self)
        self.lblThermistorValue11.move(440, 100 + 7 * 20)
        self.lblThermistorValue11.resize(100, 30)

        # Thermistor 12
        self.lblThermistor12 = QtGui.QLabel("12: ", self)
        self.lblThermistor12.move(410, 100 + 8 * 20)
        self.lblThermistor12.resize(100, 30)

        # Thermistor Value 12
        self.lblThermistorValue12 = QtGui.QLabel("0", self)
        self.lblThermistorValue12.move(440, 100 + 8 * 20)
        self.lblThermistorValue12.resize(100, 30)

        # Thermistor 13
        self.lblThermistor13 = QtGui.QLabel("13: ", self)
        self.lblThermistor13.move(310, 100 + 10 * 20)
        self.lblThermistor13.resize(100, 30)

        # Thermistor Value 13
        self.lblThermistorValue13 = QtGui.QLabel("0", self)
        self.lblThermistorValue13.move(340, 100 + 10 * 20)
        self.lblThermistorValue13.resize(100, 30)

        # Thermistor 14
        self.lblThermistor14 = QtGui.QLabel("14: ", self)
        self.lblThermistor14.move(310, 100 + 11 * 20)
        self.lblThermistor14.resize(100, 30)

        # Thermistor Value 14
        self.lblThermistorValue14 = QtGui.QLabel("0", self)
        self.lblThermistorValue14.move(340, 100 + 11 * 20)
        self.lblThermistorValue14.resize(100, 30)

        # Thermistor 15
        self.lblThermistor15 = QtGui.QLabel("15: ", self)
        self.lblThermistor15.move(410, 100 + 10 * 20)
        self.lblThermistor15.resize(100, 30)

        # Thermistor Value 15
        self.lblThermistorValue15 = QtGui.QLabel("0", self)
        self.lblThermistorValue15.move(440, 100 + 10 * 20)
        self.lblThermistorValue15.resize(100, 30)

        # Thermistor 16
        self.lblThermistor16 = QtGui.QLabel("16: ", self)
        self.lblThermistor16.move(410, 100 + 11 * 20)
        self.lblThermistor16.resize(100, 30)

        # Thermistor Value 16
        self.lblThermistorValue16 = QtGui.QLabel("0", self)
        self.lblThermistorValue16.move(440, 100 + 11 * 20)
        self.lblThermistorValue16.resize(100, 30)

        # Fan label
        self.lblFanLabel = QtGui.QLabel("Fan Command: ", self)
        self.lblFanLabel.move(515, 100)
        self.lblFanLabel.resize(100, 30)

        # Fan Speed Value 1
        self.lblFanSpeedValue1 = QtGui.QLabel("0%", self)
        self.lblFanSpeedValue1.move(515, 100 + 2 * 20)
        self.lblFanSpeedValue1.resize(100, 45)

        # Fan Speed Value 2
        self.lblFanSpeedValue2 = QtGui.QLabel("0%", self)
        self.lblFanSpeedValue2.move(565, 100 + 2 * 20)
        self.lblFanSpeedValue2.resize(100, 45)

        # Fan Speed Value 3
        self.lblFanSpeedValue3 = QtGui.QLabel("0%", self)
        self.lblFanSpeedValue3.move(515, 100 + 5 * 20)
        self.lblFanSpeedValue3.resize(100, 45)

        # Fan Speed Value 4
        self.lblFanSpeedValue4 = QtGui.QLabel("0%", self)
        self.lblFanSpeedValue4.move(565, 100 + 5 * 20)
        self.lblFanSpeedValue4.resize(100, 45)

        # Fan Speed Value 5
        self.lblFanSpeedValue5 = QtGui.QLabel("0%", self)
        self.lblFanSpeedValue5.move(515, 100 + 8 * 20)
        self.lblFanSpeedValue5.resize(100, 45)

        # Fan Speed Value 6
        self.lblFanSpeedValue6 = QtGui.QLabel("0%", self)
        self.lblFanSpeedValue6.move(565, 100 + 8 * 20)
        self.lblFanSpeedValue6.resize(100, 45)

        # Fan Speed Value 7
        self.lblFanSpeedValue7 = QtGui.QLabel("0%", self)
        self.lblFanSpeedValue7.move(515, 100 + 11 * 20)
        self.lblFanSpeedValue7.resize(100, 45)

        # Fan Speed Value 8
        self.lblFanSpeedValue8 = QtGui.QLabel("0%", self)
        self.lblFanSpeedValue8.move(565, 100 + 11 * 20)
        self.lblFanSpeedValue8.resize(100, 45)

        # Independent Bias current label
        self.lblIndependentBiasCurrent = QtGui.QLabel("Bias Current (A): ", self)
        self.lblIndependentBiasCurrent.move(630, 100)
        self.lblIndependentBiasCurrent.resize(150, 30)

        # Bias current textbox 1
        self.txtBiasCurrent1 = QtGui.QLineEdit(self)
        self.txtBiasCurrent1.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent1.move(630, 110 + 1 * 20)
        self.txtBiasCurrent1.resize(30, 15)

        # Bias current textbox 2
        self.txtBiasCurrent2 = QtGui.QLineEdit(self)
        self.txtBiasCurrent2.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent2.move(630, 110 + 2 * 20)
        self.txtBiasCurrent2.resize(30, 15)

        # Bias current textbox 3
        self.txtBiasCurrent3 = QtGui.QLineEdit(self)
        self.txtBiasCurrent3.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent3.move(630, 110 + 3 * 20)
        self.txtBiasCurrent3.resize(30, 15)

        # Bias current textbox 4
        self.txtBiasCurrent4 = QtGui.QLineEdit(self)
        self.txtBiasCurrent4.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent4.move(630, 110 + 4 * 20)
        self.txtBiasCurrent4.resize(30, 15)

        # Bias current textbox 5
        self.txtBiasCurrent5 = QtGui.QLineEdit(self)
        self.txtBiasCurrent5.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent5.move(630, 110 + 5 * 20)
        self.txtBiasCurrent5.resize(30, 15)

        # Bias current textbox 6
        self.txtBiasCurrent6 = QtGui.QLineEdit(self)
        self.txtBiasCurrent6.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent6.move(630, 110 + 6 * 20)
        self.txtBiasCurrent6.resize(30, 15)

        # Bias current textbox 7
        self.txtBiasCurrent7 = QtGui.QLineEdit(self)
        self.txtBiasCurrent7.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent7.move(630, 110 + 7 * 20)
        self.txtBiasCurrent7.resize(30, 15)

        # Bias current textbox 8
        self.txtBiasCurrent8 = QtGui.QLineEdit(self)
        self.txtBiasCurrent8.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent8.move(630, 110 + 8 * 20)
        self.txtBiasCurrent8.resize(30, 15)

        # Bias current textbox 9
        self.txtBiasCurrent9 = QtGui.QLineEdit(self)
        self.txtBiasCurrent9.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent9.move(630, 110 + 9 * 20)
        self.txtBiasCurrent9.resize(30, 15)

        # Bias current textbox 10
        self.txtBiasCurrent10 = QtGui.QLineEdit(self)
        self.txtBiasCurrent10.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent10.move(630, 110 + 10 * 20)
        self.txtBiasCurrent10.resize(30, 15)

        # Bias current textbox 11
        self.txtBiasCurrent11 = QtGui.QLineEdit(self)
        self.txtBiasCurrent11.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent11.move(630, 110 + 11 * 20)
        self.txtBiasCurrent11.resize(30, 15)

        # Bias current textbox 12
        self.txtBiasCurrent12 = QtGui.QLineEdit(self)
        self.txtBiasCurrent12.setText(DEFAULT_BIAS_CURRENT)
        self.txtBiasCurrent12.move(630, 110 + 12 * 20)
        self.txtBiasCurrent12.resize(30, 15)

        # Variable declarations
        self.intBiasOnTimerSeconds = 0  # # of seconds supply has been on
        self.intBiasOffTimerSeconds = 0
        self.intBiasCurrentState = 0  # Desired state of power supply (on = 1)

        # Shows the main form
        self.setGeometry(600, 50, 900, 700)
        self.show()
        self.activateWindow()



        #  self.layout = QtGui.QVBoxLayout(self)

        # Start push button
        self.btnStart = QtGui.QPushButton("Start", self)
        self.btnStart.clicked.connect(self.btnStartClicked)
        self.btnStart.resize(100, 45)
        self.btnStart.move(130, 10)
        ##
##        # Print iterations in the GUI
##        self.lbliteration = QtGui.QLabel("Iteration: ", self)
##        self.valueiteration = QtGui.QLabel(str(self.counter), self)
##        self.lbliteration.move(30, 100 + 1 * 20)
##        self.lbliteration.resize(130, 30)
##        self.valueiteration.move(30, 100 + 2 * 20)
##        self.valueiteration.resize(130, 30)

        # Starts the main timer
        self.intArduinoTimerEnabled = 0
        self.intTDKTimerEnabled = 0
        self.intRun = 1
        self.threadPool.append(GenericThread(self.tmrMainTimer))
        self.disconnect(self, QtCore.SIGNAL("UpdateGUI()"), self.UpdateGUI)
        self.connect(self, QtCore.SIGNAL("UpdateGUI()"), self.UpdateGUI)
        self.threadPool[len(self.threadPool) - 1].start()

    def serCheckCOMPorts(self, COMPORT="COM20", TDKADDR=1, BAUDRATE=57600):
        ser = serial.Serial()
        ser.baudrate = BAUDRATE
        ser.port = COMPORT
        ser.timeout = 1
        report_open = ser.isOpen
        if report_open == True:
            ser.close()
        ser.open()

        time.sleep(0.02)
        ser.write('ADR ' + str(TDKADDR) + '\r\n')
        time.sleep(0.02)
        connection_status = ser.readline()
        time.sleep(0.02)
        ser.write('IDN?\r\n')
        time.sleep(0.02)
        IDN_RETURNED = ser.readline()
        ##        if (VERBOSE == 1): print IDN_RETURNED
        ser.close()
        return IDN_RETURNED

    def btnReconnectClicked(self):
        NOW = str(datetime.datetime.now())
        name = "Y:\\Current Cycling\\Kat's Data\\Data\\CCData_"
        self.txtSaveFilePathName.setText(name + str(self.txtUserName.text()))
        ports = self.serGetAllPorts()
        if (VERBOSE == 1): print ports
##        if (VERBOSE == 1): print len(self.serGetAllPorts())
        ports_list = ports.split(',')
        if (VERBOSE == 1): print ports_list
        IDN_LIST = ["" for x in range(len(ports_list))]
        DEVICE_LIST = ["" for x in range(len(ports_list))]
        for i in range(len(ports_list)):
            IDN_LIST[i] = self.serCheckCOMPorts(ports_list[i], 1, 57600)
            if IDN_LIST[i][0:3] == 'TDK':
                DEVICE_LIST[i] = "TDK"
                TDK_PORT = i
            elif IDN_LIST[i][0:3] == 'ARD':
                DEVICE_LIST[i] = "ARD"
                ARDUINO_PORT = i
            else:
                DEVICE_LIST[i] = "UNKNOWN"
        if (VERBOSE == 1): print IDN_LIST
        self.IDN_LIST_ARDUINO_TDK = IDN_LIST
        timepoint = 0
        ##        if (VERBOSE == 1): print IDN_LIST[0][0:3]
        # Check TDK port for all twelve addresses
##        try:
        self.serTDK = serial.Serial()
        self.serTDK.baudrate = BAUDRATE
        self.serTDK.port = ports_list[TDK_PORT]
        self.serTDK.timeout = 1
        if (VERBOSE == 1): print 'check port open'
        report_open = self.serTDK.isOpen
        if report_open == True:
            self.serTDK.close()
        if (VERBOSE == 1): print 'try to open port'
        self.serTDK.open()
        time.sleep(0.02)
        if (VERBOSE == 1): print 'post open port'
        addresses_open = np.zeros((12))
        self.IDNs = []
        for i in range(12):
            self.serTDK.write('ADR ' + str(i + 1) + '\r\n')
            time.sleep(0.02)
            connection_status = (self.serTDK.read(self.serTDK.inWaiting()))
            time.sleep(0.02)
            self.serTDK.write('RST\r\n')
            if (VERBOSE == 1): print 'RST\r\n'
            time.sleep(0.02)
            reset_result = self.serTDK.read(self.serTDK.inWaiting())
            if (VERBOSE == 1): print reset_result
            time.sleep(0.02)
            self.serTDK.write('IDN?\r\n')
            time.sleep(0.02)
            IDN_RETURNED = (self.serTDK.read(self.serTDK.inWaiting()))
            time.sleep(0.02)
            self.serTDK.write('SN?\r\n')
            time.sleep(0.02)
            SN_RETURNED = (self.serTDK.read(self.serTDK.inWaiting()))
            time.sleep(0.02)
            self.serTDK.write('REV?\r\n')
            time.sleep(0.02)
            REV_RETURNED = (self.serTDK.read(self.serTDK.inWaiting()))
            time.sleep(0.02)
            self.serTDK.write('DATE?\r\n')
            time.sleep(0.02)
            CAL_DATE_RETURNED = (self.serTDK.read(self.serTDK.inWaiting()))
            time.sleep(0.02)
            self.IDNs.append(IDN_RETURNED)
            self.IDNs.append(SN_RETURNED)
            self.IDNs.append(REV_RETURNED)
            self.IDNs.append(CAL_DATE_RETURNED)
            self.IDNs.append("/n")
            ##                if (VERBOSE == 1): print self.IDNs
            if IDN_RETURNED[0:3] == 'TDK':
                addresses_open[i] = 1
        for j in range(len(dict_to_GUI["PowerSupplies"])):
            if addresses_open[j] == 1:
                dict_to_GUI["PowerSupplies"][j]["isConnected"] = 'Connected ' + str(j+1)
            else:
                dict_to_GUI["PowerSupplies"][j]["isConnected"] = 'Not Connected ' + str(j+1)


##        except:
##            if (VERBOSE == 1): print 'TDK address check fail'
            ##        self.TDK.serOpenTDK("COM20",1)
            ##        if (VERBOSE == 1): print self.TDK.getIDN()

        # Set up Arduino; OPEN PORT AND SEND initial values
        self.serArduino = serial.Serial()
        self.serArduino.baudrate = BAUDRATE
        self.serArduino.port = ports_list[ARDUINO_PORT]
        self.serArduino.timeout = 1
        report_open = self.serArduino.isOpen
        if report_open == True:
            self.serArduino.close()
        self.serArduino.open()

        # Starts the Arduino timer
        self.intArduinoTimerEnabled = 1

    def btnStartClicked(self):
        self.cycle_number = 1
        NOW = str(datetime.datetime.now())

        # here OutputFile is self.txtSaveFilePathName.text(), first_time_seconds is first_time_seconds
        self.WriteToFile("Cycle Number, Epoch Time (seconds), Time (hrs),Current Status," + \
                         "Current 1, Voltage 1,Current 2, Voltage 2, Current 3, Voltage 3, Current 4, Voltage 4, Current 5, Voltage 5, Current 6, Voltage 6," + \
                         "Current 7, Voltage 7, Current 8, Voltage 8, Current 9, Voltage 9, Current 10, Voltage 10, Current 11, Voltage 11, Current 12, Voltage 12," + \
                         "Temp 1, Temp 2, Temp 3, Temp 4, Temp 5, Temp 6, Temp 7, Temp 8 , Temp 9, Temp 10, Temp 11, Temp 12," + \
                         "Temp 13, Temp 14, Temp 15, Temp 16\n", self.txtSaveFilePathName.text(), first_time_seconds)

        # Meta data file; here OutputFile is self.txtSaveFilePathName.text(), first_time_seconds is first_time_seconds
        self.WriteToFile("Datetime: " + str(NOW) + "\n" \
                         + "User: " + str(self.txtUserName.text()) + "\n" \
                         + str(self.IDN_LIST_ARDUINO_TDK) + "\n" \
                         + "Current Cycling Controls Python Firmware Version: " + str(
            CCCabinetPythonControlsVersion) + "\n" \
                         + "TDK IDNs\n" + str(self.IDNs) + "\n" \
                         + "Current On Temp Setpoint: " + str(self.txtCurrentOnTempSetpoint.text()) + "\n" \
                         + "Current Off Temp Setpoint: " + str(self.txtCurrentOffTempSetpoint.text()) + "\n" \
                         + "Overtemp Setpoint: " + str(self.txtOvertempSetpoint.text()) + "\n" \
                         + "Current settings: \n" \
                         + str(self.txtBiasCurrent1.text()) + "\n" \
                         + str(self.txtBiasCurrent2.text()) + "\n" \
                         + str(self.txtBiasCurrent3.text()) + "\n" \
                         + str(self.txtBiasCurrent4.text()) + "\n" \
                         + str(self.txtBiasCurrent5.text()) + "\n" \
                         + str(self.txtBiasCurrent6.text()) + "\n" \
                         + str(self.txtBiasCurrent7.text()) + "\n" \
                         + str(self.txtBiasCurrent8.text()) + "\n" \
                         + str(self.txtBiasCurrent9.text()) + "\n" \
                         + str(self.txtBiasCurrent10.text()) + "\n" \
                         + str(self.txtBiasCurrent11.text()) + "\n" \
                         + str(self.txtBiasCurrent12.text()) + "\n" \
                         + "Bias On Time (min): " + str(self.txtBiasOnTime.text()) + "\n" \
                         + "Bias Off Time (min): " + str(self.txtBiasOffTime.text()) + "\n" \
                         , self.txtSaveFilePathName.text() + 'Meta', first_time_seconds)

        self.intTDKTimerEnabled = 1

        self.intBiasCurrentState = int(1)

        # Send settings to Arduino when start button is pressed only
        if (VERBOSE == 1): print "trying to write to arduino"
        self.serArduino.write('START\r\n')
        time.sleep(0.02)
        self.serArduino.write('WRITE_TO_ARDUINO\r\n')
        time.sleep(0.02)
        if (VERBOSE == 1): print "intBiasCurrentState ="
        if (VERBOSE == 1): print str(self.intBiasCurrentState)
        self.serArduino.write(
            str(int(self.intBiasCurrentState)) + ',' + str(int(self.txtCurrentOnTempSetpoint.text())) + ',' + str(
                int(self.txtCurrentOffTempSetpoint.text())) + ',' + str(
                int(self.txtOvertempSetpoint.text())) + ',' + '\r\n')
        time.sleep(0.02)
        if (VERBOSE == 1): print "wrote to arduino"

    def btnStopClicked(self):
        self.intBiasCurrentState = 0
        self.intArduinoTimerEnabled = 0
        self.intTDKTimerEnabled = 0
        self.serArduino.close()
        for i in range(12):
            self.serTDK.write('ADR ' + str(i) + '\r\n')
            time.sleep(0.01)
            self.serTDK.write('OUT OFF\r\n')
            time.sleep(0.01)
        self.serTDK.close()


     # ====================END OF USER INTERFACE FUNCTIONS========================

    # ================BEGINNING OF ALL PURPOSE FUNCTIONS=========================
    # Function to list all COM ports
    def serGetAllPorts(self):
        listallports = (
            ",".join(
                [
                    port.device
                    for port in list_ports.comports()
                ]))

        return listallports

    def SendPowerPowerSupplyCommand(self):
        # Collects all the currents
        if (self.intBiasCurrentState == 1):
            self.Current_Settings = [self.txtBiasCurrent1.text(), self.txtBiasCurrent2.text(),
                                     self.txtBiasCurrent3.text(), self.txtBiasCurrent4.text(), \
                                     self.txtBiasCurrent5.text(), self.txtBiasCurrent6.text(),
                                     self.txtBiasCurrent7.text(), self.txtBiasCurrent8.text(),
                                     self.txtBiasCurrent9.text(), \
                                     self.txtBiasCurrent10.text(), self.txtBiasCurrent11.text(),
                                     self.txtBiasCurrent12.text()]
        else:
            self.Current_Settings = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        #

        TDK_DATA = np.zeros((12, 6))

        for i in range(12):
            ##            try:

            self.serTDK.write('ADR ' + str(i + 1) + '\r\n')
            time.sleep(0.02)
            ##            if (VERBOSE == 1): print 'ADR ' + str(i+1) + '\r\n'
            ADR_return = self.serTDK.read(self.serTDK.inWaiting())
            if (VERBOSE == 1): print ADR_return
            time.sleep(0.02)

            self.serTDK.write('IDN?\r\n')
            time.sleep(0.02)
            ##            if (VERBOSE == 1): print 'IDN?\r\n'
            ##            time.sleep(0.02)
            IDN_RETURNED = (self.serTDK.read(self.serTDK.inWaiting()))
            time.sleep(0.02)
            ##            if (VERBOSE == 1): print IDN_RETURNED
            ##            time.sleep(0.02)
            if IDN_RETURNED[0:3] == 'TDK':
                # Set interlock
                if self.chkTDKInterlockActive.isChecked():
                    self.serTDK.write('RIE ON\r\n')
                    time.sleep(0.02)
                else:
                    self.serTDK.write('RIE OFF\r\n')
                    time.sleep(0.02)
                self.serTDK.write('RIE?\r\n')
                time.sleep(0.02)
                if (VERBOSE == 1): print "remote interlock on?"
                remote_interlock = self.serTDK.read(self.serTDK.inWaiting())
                if (VERBOSE == 1): print remote_interlock
                time.sleep(0.02)
                # Set compliance voltage
                self.serTDK.write('PV ' + str(VOLTAGE_COMPLIANCE) + '\r\n')
                time.sleep(0.2)
                ##                if (VERBOSE == 1): print 'PV ' + str(VOLTAGE_COMPLIANCE) + '\r\n'
                ##                if (VERBOSE == 1): print self.serTDK.read(self.serTDK.inWaiting())
                time.sleep(0.02)
                # Set current
                self.serTDK.write('PC ' + str(self.Current_Settings[i]) + '\r\n')
                time.sleep(0.2)
                ##                if (VERBOSE == 1): print 'PC ' + str(self.Current_Settings[i]) + '\r\n'
                ##                if (VERBOSE == 1): print self.serTDK.read(self.serTDK.inWaiting())
                time.sleep(0.02)
                # Turn on output
                if self.intBiasCurrentState == 1:
                    self.serTDK.write('OUT ON\r\n')
                    dict_to_GUI["CurrentBiasStatus"] = "On"
                    time.sleep(0.2)
                else:
                    self.serTDK.write('OUT OFF\r\n')
                    dict_to_GUI["CurrentBiasStatus"] = "Off"
                    time.sleep(0.2)
                    ##                if (VERBOSE == 1): print 'OUT ON\r\n'
                a = self.serTDK.read(self.serTDK.inWaiting())
                time.sleep(0.02)
                # Read TDK Data
                self.serTDK.write('DVC?\r\n')
                time.sleep(0.02)
                ##                if (VERBOSE == 1): print 'DVC?\r\n'
                TDK_OUTPUT = self.serTDK.readline()
                time.sleep(0.2)
                ##                if (VERBOSE == 1): print TDK_OUTPUT
                TDK_OUTPUT_LIST = TDK_OUTPUT.split(',')
                ##                if (VERBOSE == 1): print "TDK_OUTPUT_LIST"
                if (VERBOSE == 1): print TDK_OUTPUT_LIST
                for j in range(6):

                    TDK_DATA[i, j] = float(TDK_OUTPUT_LIST[j])

        time_now = round(time.time(), 0)  #
        hrs_now = (round(time.time(), 0) - float(first_time_seconds)) / 3600  # time in hrs
        if (VERBOSE == 1): print "hours ran"
        if (VERBOSE == 1): print hrs_now
##        print "dict to gui temp 15"
##        print dict_to_GUI["Temperatures"][15]
        if self.intBiasOnTimerSeconds%SAVETIME == 0 and self.intBiasOffTimerSeconds%SAVETIME == 0:
            try:
                self.WriteToFile(str(dict_to_GUI["CycleNumber"]) + "," + str(time_now) + "," + str(hrs_now) + "," + str(dict_to_GUI["CurrentBiasStatus"]) + "," + \
                str(TDK_DATA[0,2]) +","+ str(TDK_DATA[0,0])+"," +str(TDK_DATA[1,2]) +","+ str(TDK_DATA[1,0])+"," +str(TDK_DATA[2,2]) +","+ str(TDK_DATA[2,0])+"," +\
                str(TDK_DATA[3,2]) +","+ str(TDK_DATA[3,0])+"," +str(TDK_DATA[4,2]) +","+ str(TDK_DATA[4,0])+"," +str(TDK_DATA[5,2]) +","+ str(TDK_DATA[5,0])+"," +\
                str(TDK_DATA[6,2]) +","+ str(TDK_DATA[6,0])+"," +str(TDK_DATA[7,2]) +","+ str(TDK_DATA[7,0])+"," +str(TDK_DATA[8,2]) +","+ str(TDK_DATA[8,0])+"," +\
                str(TDK_DATA[9,2]) +","+ str(TDK_DATA[9,0])+"," +str(TDK_DATA[10,2]) +","+ str(TDK_DATA[10,0])+"," +str(TDK_DATA[11,2]) +","+ str(TDK_DATA[11,0])+"," +\
                str(dict_to_GUI["Temperatures"][0])+","+str(dict_to_GUI["Temperatures"][1])+","+str(dict_to_GUI["Temperatures"][2])+","+str(dict_to_GUI["Temperatures"][3])+","+\
                str(dict_to_GUI["Temperatures"][4])+","+str(dict_to_GUI["Temperatures"][5])+","+str(dict_to_GUI["Temperatures"][6])+","+str(dict_to_GUI["Temperatures"][7])+","+\
                str(dict_to_GUI["Temperatures"][8])+","+str(dict_to_GUI["Temperatures"][9])+","+str(dict_to_GUI["Temperatures"][10])+","+str(dict_to_GUI["Temperatures"][11])+","+\
                str(dict_to_GUI["Temperatures"][12])+","+str(dict_to_GUI["Temperatures"][13])+","+str(dict_to_GUI["Temperatures"][14])+","+str(dict_to_GUI["Temperatures"][15])+","+\
                "\n",self.txtSaveFilePathName.text(),first_time_seconds)
            except:
                self.WriteToFile(str(dict_to_GUI["CycleNumber"]) + "," + str(time_now) + "," + str(hrs_now) + "," + str(dict_to_GUI["CurrentBiasStatus"]) + "," + \
                str(TDK_DATA[0,2]) +","+ str(TDK_DATA[0,0])+"," +str(TDK_DATA[1,2]) +","+ str(TDK_DATA[1,0])+"," +str(TDK_DATA[2,2]) +","+ str(TDK_DATA[2,0])+"," +\
                str(TDK_DATA[3,2]) +","+ str(TDK_DATA[3,0])+"," +str(TDK_DATA[4,2]) +","+ str(TDK_DATA[4,0])+"," +str(TDK_DATA[5,2]) +","+ str(TDK_DATA[5,0])+"," +\
                str(TDK_DATA[6,2]) +","+ str(TDK_DATA[6,0])+"," +str(TDK_DATA[7,2]) +","+ str(TDK_DATA[7,0])+"," +str(TDK_DATA[8,2]) +","+ str(TDK_DATA[8,0])+"," +\
                str(TDK_DATA[9,2]) +","+ str(TDK_DATA[9,0])+"," +str(TDK_DATA[10,2]) +","+ str(TDK_DATA[10,0])+"," +str(TDK_DATA[11,2]) +","+ str(TDK_DATA[11,0])+"," +\
                str(dict_to_GUI["Temperatures"][0])+","+str(dict_to_GUI["Temperatures"][1])+","+str(dict_to_GUI["Temperatures"][2])+","+str(dict_to_GUI["Temperatures"][3])+","+\
                str(dict_to_GUI["Temperatures"][4])+","+str(dict_to_GUI["Temperatures"][5])+","+str(dict_to_GUI["Temperatures"][6])+","+str(dict_to_GUI["Temperatures"][7])+","+\
                str(dict_to_GUI["Temperatures"][8])+","+str(dict_to_GUI["Temperatures"][9])+","+str(dict_to_GUI["Temperatures"][10])+","+str(dict_to_GUI["Temperatures"][11])+","+\
                str(dict_to_GUI["Temperatures"][12])+","+str(dict_to_GUI["Temperatures"][13])+","+str(dict_to_GUI["Temperatures"][14])+","+str(dict_to_GUI["Temperatures"][15])+","+\
                "\n","C:\\Users\\python\\Documents\\CC Cabinet\\Data\\CCData_"+self.txtUserName.text(),first_time_seconds)
                print "had to save to local drive"

            if (VERBOSE == 1): print str(datetime.datetime.now())

        time.sleep(0.01)
        ##        if (VERBOSE == 1): print TDK_DATA
        time.sleep(0.01)
        for i in range(len(dict_to_GUI["PowerSupplies"])):
            dict_to_GUI["PowerSupplies"][i]["Current"] = str(TDK_DATA[i, 2])
            dict_to_GUI["PowerSupplies"][i]["Voltage"] = str(TDK_DATA[i, 0])


    # TDK Timer function - this definition runs every second
    def tmrTDKOneSecond(self):
        ON_TIME = float(self.txtBiasOnTime.text())
        OFF_TIME = float(self.txtBiasOffTime.text())
        TIME_NOW_SECONDS = round(time.time(), 0)

        if (TIME_NOW_SECONDS - float(first_time_seconds)) / 60.0 >= (int(self.cycle_number) - 1) * (
                    float(ON_TIME) + float(OFF_TIME)) + ON_TIME and (
                    TIME_NOW_SECONDS - float(first_time_seconds)) / 60.0 < int(self.cycle_number) * (
            ON_TIME + OFF_TIME):
            self.intBiasCurrentState = 0

        elif (TIME_NOW_SECONDS - float(first_time_seconds)) / 60.0 >= int(self.cycle_number) * (
                    ON_TIME + OFF_TIME):
            self.cycle_number = self.cycle_number + 1
            self.intBiasCurrentState = 1
        else:
            if (VERBOSE == 1): print "timer doesn't make sense"
        if (VERBOSE == 1): print "intBiasCurrentState"
        if (VERBOSE == 1): print str(self.intBiasCurrentState)


        dict_to_GUI["CycleNumber"] = str(self.cycle_number)
        dict_to_GUI["MinutesIntoCycle"] = (TIME_NOW_SECONDS - float(first_time_seconds)) / 60.0 - float(
            self.cycle_number - 1.0) * (ON_TIME + OFF_TIME)

        # Sends the power commands
        self.SendPowerPowerSupplyCommand()

    # Arduino Timer function - this definition runs every second
    def tmrArduinoOneSecond(self):
        # Write/read to Arduino
##        try:
            ##            if (VERBOSE == 1): print "trying to open and read from arduino port"
        # Write to Arduino
        if (VERBOSE == 1): print "trying to write to arduino"
        self.serArduino.write('WRITE_TO_ARDUINO\r\n')
        time.sleep(0.02)
        if (VERBOSE == 1): print "intBiasCurrentState = " + str(self.intBiasCurrentState)
##        if (VERBOSE == 1): print str(self.intBiasCurrentState)

        self.serArduino.write(
            str(int(self.intBiasCurrentState)) + ',' + str(int(self.txtCurrentOnTempSetpoint.text())) + ',' + str(
                int(self.txtCurrentOffTempSetpoint.text())) + ',' + str(
                int(self.txtOvertempSetpoint.text())) + ',' + '\r\n')
        time.sleep(0.02)
        if (VERBOSE == 1): print "wrote to arduino"

        # Read from Arduino
        self.serArduino.write('READ_TO_PC\r\n')
        time.sleep(0.1)
        self.strDataFromArduino = self.serArduino.readline()
        time.sleep(0.1)
        print 'printing arduiono output'
        print str(self.strDataFromArduino)

        # Parses data from Arduino
        self.SplitDataFromArduino = self.strDataFromArduino.split(',')
        if (VERBOSE == 1): print len(self.SplitDataFromArduino)
        ##            if (VERBOSE == 1): print len(self.SplitDataFromArduino)

        dict_to_GUI["Temperatures"][0:16] = self.SplitDataFromArduino[0:16]
##        print dict_to_GUI["FanSpeeds"]


        dict_to_GUI["FanSpeeds"][0:8] = self.SplitDataFromArduino[16:24]
##        print dict_to_GUI["FanSpeeds"]


        if (VERBOSE == 1): print "check arduino current bias status"
        self.ArduinoCurrentBiasStatus = self.SplitDataFromArduino[24]


        if (VERBOSE == 1): print "Arduino current bias status "
        if (VERBOSE == 1): print str(self.ArduinoCurrentBiasStatus)
        dict_to_GUI["CurrentBiasState"] = self.ArduinoCurrentBiasStatus
        self.intSmokeSensorLockoutStatus = self.SplitDataFromArduino[25]
        if (VERBOSE == 1): print "Arduino smoke sensor lockout status "
        if (VERBOSE == 1): print str(self.intSmokeSensorLockoutStatus)


##        except:
##            if (VERBOSE == 1): print 'Arduino port open fail'

##        print dict_to_GUI

    # Main one second timer
    def tmrMainTimer(self):
        while True:
            # Runs the Arduino timer code
            if (self.intArduinoTimerEnabled == 1):
                if (VERBOSE == 1): print 'Arduino timer enabled'
                self.tmrArduinoOneSecond()
                time.sleep(0.001)

            # Runs the TDK timer code
            if (self.intTDKTimerEnabled == 1):
                self.tmrTDKOneSecond()
                time.sleep(0.001)
##            # Allows for GUI to refresh
##            QApplication.processEvents()

            # if (VERBOSE == 1): prints if we're in a separate thread
            if (VERBOSE == 1): print 'Timer active'

            # Runs the timer, and checks to see if we're exiting
            if (self.intRun == 1):
                # threading.Timer(TMRONESECOND_INTERVAL, self.tmrMainTimer).start()
                time.sleep(TMRONESECOND_INTERVAL)
            else:
                break

            self.emit(QtCore.SIGNAL('UpdateGUI()'))

    def UpdateGUI(self):
        for i in range(len(dict_to_GUI["PowerSupplies"])):
            getattr(self, "lblPowerSupply"+str(i+1)).setText(str(dict_to_GUI["PowerSupplies"][i]["isConnected"]))
            getattr(self, "lblCurrent" + str(i + 1)).setText(str(dict_to_GUI["PowerSupplies"][i]["Current"]))
            getattr(self, "lblVoltage" + str(i + 1)).setText(str(dict_to_GUI["PowerSupplies"][i]["Voltage"]))
        for i in range(len(dict_to_GUI["Temperatures"])):
            getattr(self, "lblThermistorValue" + str(i + 1)).setText(str(dict_to_GUI["Temperatures"][i]))
        for i in range(len(dict_to_GUI["FanSpeeds"])):
            getattr(self, "lblFanSpeedValue" + str(i + 1)).setText(str(dict_to_GUI["FanSpeeds"][i])+ '%')

        self.lblCycleNumber.setText(str(dict_to_GUI["CycleNumber"]))
        self.lblCycleTime.setText(str(round(dict_to_GUI["MinutesIntoCycle"], 2)))
        self.lblBiasState.setText(str(dict_to_GUI["CurrentBiasStatus"]))



    def btnExitClicked(self):
        # Automatically run stop
        if (self.intTDKTimerEnabled == 1):
            self.btnStopClicked()

        # Tells the timer thread to quit
        self.intRun = 0

        # Exits the app gracefully
        QtCore.QCoreApplication.instance().quit()

         # ====================END OF ALL PURPOSE FUNCTIONS===========================

class GenericThread(QtCore.QThread):
    def __init__(self, function, *args, **kwargs):
        QtCore.QThread.__init__(self)
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def run(self):
        self.function(*self.args, **self.kwargs)
        return


# run
app = QtGui.QApplication(sys.argv)
test1 = Window()
test1.show()
app.exec_()
