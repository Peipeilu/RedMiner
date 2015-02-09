import sys
import os
import time

from datetime import timedelta

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from Ui_Selection_Window import Ui_Dialog
from Function import *
from Utility import *

        
class SelectionWindow(QDialog, Ui_Dialog):
    accpeted = QtCore.pyqtSignal()
    rejected = QtCore.pyqtSignal()
    reseted = QtCore.pyqtSignal()
    yes_to_all = QtCore.pyqtSignal()
    no_to_all = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super(SelectionWindow, self).__init__(parent)
        self.setupUi(self)
        self.init_variables()
        
    def init_variables(self):
        self.select_name_list = []
        self.select_id_list = []
        
    def setup_widget(self, title, content_matrix, check_texts = []):
        self.setWindowTitle("%s Menu" %title)
        attribute_name = "%s Name"%title
        attribute_id = "%s ID"%title
        column = len(content_matrix)
        row = len(content_matrix[0])
        self.checkableTableWidget.setup(row, column, content_matrix, [attribute_name,attribute_id])
        self.checkableTableWidget.hide_column(1)
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox_2.button(QtGui.QDialogButtonBox.Reset).clicked.connect(self.reset)
        self.buttonBox_2.button(QtGui.QDialogButtonBox.YesToAll).clicked.connect(self.yes_to_all)
        self.buttonBox_2.button(QtGui.QDialogButtonBox.NoToAll).clicked.connect(self.no_to_all)        
        
        if check_texts:
            self.checkableTableWidget.check_texts(check_texts)
        
        self.checkableTableWidget.setColumnWidth([225])
        
#         if column == 1:
#             self.checkableTableWidget.setColumnWidth([225])
#         elif column == 2:
#             self.checkableTableWidget.setColumnWidth([155,70])
#         elif column == 3:
#             self.checkableTableWidget.setColumnWidth([155,35,35])
#         else:
#             self.checkableTableWidget.setColumnWidth([225/column]*column)
        
    def clear_wideget(self):
        self.select_name_list = []
        self.select_id_list = []
        self.checkableTableWidget.clear()
    
    def update_wideget(self, title, rows, columns, content, check_texts):
        self.setWindowTitle(title)
        self.checkableTableWidget.clear()
        self.checkableTableWidget.setup(rows, columns, content)
        if check_texts:
            self.checkableTableWidget.check_texts(check_texts)
    
    def fetch_result(self):
        self.select_name_list = self.checkableTableWidget.itemNameClicked()    # return Name
        self.select_id_list = self.checkableTableWidget.itemIdClicked()    # return id
#         self.checked_index_list = self.checkableTableWidget.itemIndexChecked()
        
    def accept(self, parent = None):
        self.fetch_result()
        self.accpeted.emit()
        super(SelectionWindow, self).accept()
        
    def reject(self, parent = None):
        self.rejected.emit()
        super(SelectionWindow, self).reject()
        
    def reset(self, parent = None):
        self.checkableTableWidget.reset()
    
    def yes_to_all(self, parent = None):
        self.checkableTableWidget.yes_to_all()
        
    def no_to_all(self, parent = None):
        self.checkableTableWidget.no_to_all()    
        