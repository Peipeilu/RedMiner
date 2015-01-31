import sys
import os
import time

from datetime import timedelta

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import QMainWindow

from Ui_Credential_Window import Ui_Dialog

from Utility import *
from Function import *

class CredentialWindow(QDialog, Ui_Dialog):
    credential_accpeted = QtCore.pyqtSignal(str)
    credential_rejected = QtCore.pyqtSignal()

    def __init__(self, parent = None, credential = None):
        super(CredentialWindow, self).__init__(parent)
        self.setupUi(self)
        self.credential = credential
        self.init_variables()
        self.show_date()
        
    def init_variables(self):
        pass
        
    def show_date(self):
#         print "credential-%s" %(self.credential)
        self.lineEdit.setText(self.credential)

    def accept(self, parent = None):
        print "accpet"
        credential_str = str(self.lineEdit.text())
        
        if len(credential_str) != 40:
            self.__show_warning_message("Credential key length is not correct! Please re-enter a valid key.")
#         # check_credential_sim - check length of key # check_credential_complete - send a real request to check (slow)
#         elif not check_credential_complete(credential_str):  
#             self.__show_warning_message("Checking Credential key fails.Please re-enter a valid key.")
        else:
            self.credential = credential_str
            self.credential_accpeted.emit(self.credential)
            super(CredentialWindow, self).accept()
        
    def reject(self, parent = None):
        print "reject"
        self.credential_rejected.emit()
        super(CredentialWindow, self).reject()

    def __show_warning_message(self, message):
        reply = QtGui.QMessageBox.warning(self, 'Warning', message, QtGui.QMessageBox.Yes)
        if reply == QtGui.QMessageBox.Yes:
            print "YES"
               
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = CredentialWindow()
    myapp.show()
    sys.exit(app.exec_())    