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

from PyQt4 import QtCore, QtGui
import sys, time

class mythread(QtCore.QThread):

    total = QtCore.pyqtSignal(object)
    update = QtCore.pyqtSignal()

    def __init__(self, parent, n):
        super(mythread, self).__init__(parent)
        self.n = n

    def run(self):
        self.total.emit(self.n)
        i = 0
        while (i<self.n):
            if (time.time() % 1==0):
                i+=1
                #print str(i)
                self.update.emit()

# create the dialog for zoom to point
class progress(QtGui.QProgressBar):

    def __init__(self, parent=None):
        super(progress, self).__init__(parent)
        # Set up the user interface from Designer.
        self.setValue(0)

        self.thread = mythread(self, 3)

        self.thread.total.connect(self.setMaximum)
        self.thread.update.connect(self.update)
        self.thread.finished.connect(self.close)

        self.n = 0
        self.thread.start()

    def update(self):
        self.n += 1
        print self.n
        self.setValue(self.n)

if __name__=="__main__":
    app = QtGui.QApplication([])
    progressWidget = progress()
    progressWidget.move(300, 300)
    progressWidget.show()
    sys.exit(app.exec_())