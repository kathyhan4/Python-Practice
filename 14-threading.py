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

from PySide.QtCore import *
from PySide.QtGui import *
import sys

import showGui

class MainDialog(QDialog, showGui.Ui_mainDialog):

    def __init__(self, parent=None):
        super(MainDialog, self).__init__(parent)
        self.setupUi(self)

        self.connect(self.showButton, SIGNAL("clicked()"), self.processData)

    def prodessData(self):
        QMessageBox.information(self, "Hello!", "Hello there, " + self.nameEdit.text())


app = QApplication(sys.argv)
form = MainDialog()
form.show()
app.exec_()

