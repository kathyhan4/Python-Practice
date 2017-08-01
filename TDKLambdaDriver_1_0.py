#-------------------------------------------------------------------------------
# Name:        TDKLambdaDriver
# Purpose:
#
# Author:      khan
#
# Created:     30/04/2017
# Copyright:   (c) khan 2017
#-------------------------------------------------------------------------------
import serial
import time

serTDK = serial.Serial()

def setAddress(addressvalue=5):
    global serTDK

    serTDK.write('ADR ' + str(addressvalue) + '\r\n')
    return (serTDK.read(serTDK.inWaiting()))

def getIDN():
    global serTDK

    serTDK.write('IDN?\r\n')
    time.sleep(0.2)
    return (serTDK.read(serTDK.inWaiting()))

def setVoltage(voltagevalue=5.0):
    global serTDK

    serTDK.write('PV ' + str(voltagevalue) + '\r\n')
    time.sleep(0.2)
    return (serTDK.read(serTDK.inWaiting()))

def setCurrent(currentvalue=0.001):
    global serTDK

    serTDK.write('PC ' + str(currentvalue) + '\r\n')
    time.sleep(0.2)
    return (serTDK.read(serTDK.inWaiting()))

def setOutputOn():
    global serTDK

    serTDK.write('OUT ON\r\n')
    time.sleep(0.2)
    serTDK.read(serTDK.inWaiting())

def setOutputOff():
    global serTDK

    serTDK.write('OUT OFF\r\n')
    time.sleep(0.2)
    serTDK.read(serTDK.inWaiting())

def getVoltage():
    global serTDK

    serTDK.write('MV?\r\n')
    time.sleep(0.2)
    return (serTDK.read(serTDK.inWaiting()))

def getCurrent():
    global serTDK

    serTDK.write('MC?\r\n')
    time.sleep(0.2)
    return (serTDK.read(serTDK.inWaiting()))

def serOpenTDK(TDKCOM="COM20", TDKADDR=1, TDKBAUD=57600):
    global serTDK

    serTDK.baudrate = TDKBAUD
    serTDK.port = TDKCOM
    serTDK.timeout = 1
    report_open = serTDK.isOpen
    if report_open == True:
        serTDK.close()
    serTDK.open()
    setAddress(TDKADDR)