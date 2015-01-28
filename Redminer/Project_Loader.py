import sys
import time
import PyQt4, PyQt4.QtGui
from PyQt4 import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from Function import *
from Utility import *

class Project_Loader(QtCore.QThread):
    load_complete = QtCore.pyqtSignal(dict)
    load_fail = QtCore.pyqtSignal()
      
    def __init__(self, personal_key):
        QtCore.QThread.__init__(self)
        self.project_dict = {}
        self.personal_key = personal_key
    
    def run(self):
        print "Project_Loader runs"
        try:    
            self.project_dict = request_project_list(self.personal_key)
            
        except Exception, ex:
            MyPrint("Message:%s" %(ex), level = 'ERROR')
            self.load_fail.emit()
            
        else:
            MyPrint(self.project_dict,level = 'DEBUG')
            self.load_complete.emit(self.project_dict)

    def stop(self): 
        print "stop the drive connecting thread"
        self.project_dict = {}
        self.terminate()
        
    def __del__(self):
        self.wait()