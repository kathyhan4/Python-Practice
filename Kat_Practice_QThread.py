#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      khan
#
# Created:     25/07/2017
# Copyright:   (c) khan 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys, time
from PyQt4 import QtCore, QtGui

i = 0

class MyApp(QtGui.QWidget):
 def __init__(self, parent=None):
  QtGui.QWidget.__init__(self, parent)

  self.setGeometry(300, 300, 280, 600)
  self.setWindowTitle('threads')

  self.layout = QtGui.QVBoxLayout(self)

  self.testButton = QtGui.QPushButton("test")
  self.connect(self.testButton, QtCore.SIGNAL("released()"), self.test)
  self.listwidget = QtGui.QListWidget(self)

  self.layout.addWidget(self.testButton)
  self.layout.addWidget(self.listwidget)

  self.threadPool = []

##  #Start push button
##  self.btnStart = QtGui.QPushButton("Start", self)
##  self.btnStart.clicked.connect(self.btnStartClicked)
##  self.btnStart.resize(100,45)
##  self.btnStart.move(130,10)
##
##
##
## def btnStartClicked(self):
##  time.sleep(1)

 def add(self, text):
  """ Add item to list widget """
  print "Add: " + text
  self.listwidget.addItem(text)
  self.listwidget.sortItems()



 def addBatch2(self,text="test",iters=6,delay=0.3):
  for i in range(iters):
   time.sleep(delay) # artificial time delay
   self.emit( QtCore.SIGNAL('add(QString)'), text+" "+str(i) )

 def test(self):
  self.listwidget.clear()

  # generic thread using signal
  self.threadPool.append( GenericThread(self.addBatch2,"from generic thread using signal ",delay=0.3) )
##  self.threadPool.append( GenericThread(self.addBatch2,"from generic thread using slow signal ",delay=1.0) )
  self.disconnect( self, QtCore.SIGNAL("add(QString)"), self.add )
  self.connect( self, QtCore.SIGNAL("add(QString)"), self.add )
  self.threadPool[len(self.threadPool)-1].start()

class GenericThread(QtCore.QThread):
 def __init__(self, function, *args, **kwargs):
  QtCore.QThread.__init__(self)
  self.function = function
  self.args = args
  self.kwargs = kwargs

 def __del__(self):
  self.wait()

 def run(self):
  self.function(*self.args,**self.kwargs)
  return

# run
app = QtGui.QApplication(sys.argv)
test1 = MyApp()
test1.show()
app.exec_()