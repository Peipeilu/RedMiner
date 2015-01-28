from Ui_About import Ui_Dialog

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class AboutWindow(QDialog, Ui_Dialog):

    def __init__(self, parent = None):
        super(AboutWindow, self).__init__(parent)
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        
    def accept(self, parent = None):
        print "accpet"
        super(AboutWindow, self).accept()