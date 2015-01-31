
import sys
import os
import time
import subprocess

from datetime import timedelta
from collections import OrderedDict

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import QMainWindow

from Ui_Main_Window import Ui_Redminer
from SelectionWindow import SelectionWindow
from CredentialWindow import CredentialWindow
from AboutWindow import AboutWindow

from Function import *
from Utility import *

import Project_Loader
import Issue_Journals_Handler

__ver__ = readVersion()

__copyright__ = "Seagate Confidential, Internal Use Only "
__date__ = time.strftime("%m/%d/%Y")

if __ver__:
    __version__ = "V"+__ver__
else:
    __version__ = ""
    
__developer__ = "Jeffrey C. Ye"
__producer__ = "Cupertino Branded Software Team"
__email__ = "cong.ye@seagate.com"

print ""
print ">>>>>>>>>>>>>>>>   Redminer   <<<<<<<<<<<<<<<<<<<"
print ">>>"
print ">>>   IDHT Version: %s" %(__version__)
print ">>>   Release Date: %s" %(__date__)
print ">>>   Author: %s " %(__developer__)
print ">>>   Producer: %s" %(__producer__)
print ">>>   Email: %s" %(__email__)
print ">>>"
print ">>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<"
print ""

DIRPATH = pathProgram()

class MainWindow(QMainWindow, Ui_Redminer):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = Ui_Redminer()
        self.ui.setupUi(self)
        self.declare_variables()
        self.initilze()
        self.bindSignals()
        
    def declare_variables(self):
        '''
        declare class variables
        '''
        self.ordered_project_dict = {}  # project_dict: {project_name (str): project_id (int)}
        self.mutex = QMutex()
        self.personal_key = None
        self.loaded = False
        self.current_project_name = None
        self.current_project_id = None
        self.attribute_select_dict = {}
        self.selection_names = []
        self.selection_ids = []
        self.status_dict = {}
        self.category_dict = {}
        self.issue_journals_inst = None
        self.slider_value = 1
        self.cache_source = False
        self.setting_loaded = True
        self.last_result_path = None
        self.enable_menu = False
#         self.severity_dict = None
        self.category_dict = None
        self.status_dict = None
        self.project_journal_loading = False
        self.severity_list = None
        
    def initilze(self):
        '''
        initialize variables and UI
        '''
        self.setWindowTitle("RedMiner(Redmine Issue Tracker) %s - Produced by %s"%(__version__, __producer__))

        self.icon_pending = os.path.join(DIRPATH,"Pic","pending.png")
        self.icon_check   = os.path.join(DIRPATH,"Pic","check.png")
        self.icon_ban     = os.path.join(DIRPATH,"Pic","ban.png")
        
        self.ui.pushButton_status_switch.setIcon(QtGui.QIcon(self.icon_pending))
        self.ui.pushButton_category_switch.setIcon(QtGui.QIcon(self.icon_pending))
        self.ui.pushButton_severity_switch.setIcon(QtGui.QIcon(self.icon_pending))
        
        self.ui.pushButton_status_switch.setStyleSheet('border: 0px; padding: 0px;')
        self.ui.pushButton_category_switch.setStyleSheet('border: 0px; padding: 0px;')
        self.ui.pushButton_severity_switch.setStyleSheet('border: 0px; padding: 0px;')
        
        self.ui.pushButton_status_switch.setCursor(QtCore.Qt.ArrowCursor)
        self.ui.pushButton_category_switch.setCursor(QtCore.Qt.ArrowCursor)
        self.ui.pushButton_severity_switch.setCursor(QtCore.Qt.ArrowCursor)
        
        self.__disable_control_panel()
        self.__disable_filter_panel()
        
        self.__enable_menu()
        
        self.ui.horizontalSlider_accuracy.sliderMoved.connect(self.on_slider_moved)
        self.ui.checkBox_source.stateChanged.connect(self.on_state_changed)
        self.ui.checkBox_source.setCheckState(Qt.Unchecked)
        self.ui.checkBox_source.setEnabled(False)
        
        today = time.strftime('%Y-%m-%d',time.localtime(time.time()))
        min_day = "2013-01-01"
        
#         self.ui.pushButton_project_load.setEnabled(False)
        
        self.__disable_preference_panel()
        self.__disable_loading_panel()
        self.__disable_control_panel()
        self.__disable_filter_panel()
        self.__disable_loading_panel()
        
        clean_log()
        
        ready_credential = loadCredential()
        
        if not ready_credential:
            self.__show_warning_message("No credential key found. Please check the user guide and set one first.")

        else:
            self.personal_key = ready_credential
            self.print_to_console("Credential key is loaded")
            
            self.ui.comboBox_project.setEnabled(True)
            
            if check_settings():
                if self.__show_question_message("Saved settings found. Do you want to load it?"):
                    self.setting_loaded = True
                    self.__load_settings()
                    self.print_to_console("Load saved settings successfully")

#                     self.__disable_preference_panel()
#                     self.__disable_loading_panel()
#                     self.__disable_control_panel()
#                     self.__disable_filter_panel()
                    
                else:
                    self.print_to_console("User choose to ignore loading saved settings")
                    
                    self.ui.dateEdit_end.setDate(QtCore.QDate.fromString(today,"yyyy-MM-dd"))
                    self.__disable_preference_panel()
                    
        self.ui.dateEdit_end.setMaximumDate(QtCore.QDate.fromString(today,"yyyy-MM-dd"))
        self.ui.dateEdit_end.setMinimumDate(QtCore.QDate.fromString(min_day,"yyyy-MM-dd"))
        
        
        
    def bindSignals(self):
        self.ui.comboBox_project.activated['QString'].connect(self.on_select_project)

    def __disable_loading_panel(self):
        self.ui.pushButton_project_load.setEnabled(False)
        self.ui.comboBox_project.setEnabled(False)
        self.ui.checkBox_source.setEnabled(False)
        self.ui.textEdit_lastCopyTime.setEnabled(False)

    def __enable_loading_panel(self):
        self.ui.pushButton_project_load.setEnabled(True)
        self.ui.comboBox_project.setEnabled(True)
        self.ui.checkBox_source.setEnabled(True)
        self.ui.textEdit_lastCopyTime.setEnabled(True)
        
    def __disable_preference_panel(self):
        self.ui.dateEdit_start.setEnabled(False)
        self.ui.dateEdit_end.setEnabled(False)
        self.ui.horizontalSlider_accuracy.setEnabled(False)
        self.ui.label_unit.setEnabled(False)
        self.ui.label_accuracy.setEnabled(False)
        self.ui.dateEdit_start.setEnabled(False)
        self.ui.dateEdit_end.setEnabled(False)
        self.ui.horizontalSlider_accuracy.setEnabled(False)
                  
    def __enable_preference_panel(self):
        self.ui.dateEdit_start.setEnabled(True)
        self.ui.dateEdit_end.setEnabled(True)
        self.ui.horizontalSlider_accuracy.setEnabled(True)
        self.ui.label_unit.setEnabled(True)
        self.ui.label_accuracy.setEnabled(True)
        self.ui.dateEdit_start.setEnabled(True)
        self.ui.dateEdit_end.setEnabled(True)
        self.ui.horizontalSlider_accuracy.setEnabled(True)
                 
    def __disable_filter_panel(self):
        self.ui.pushButton_status_select.setEnabled(False)
        self.ui.pushButton_category_select.setEnabled(False)
        self.ui.pushButton_severity_select.setEnabled(False)

    def __enable_filter_panel(self):
        self.ui.pushButton_status_select.setEnabled(True)
        self.ui.pushButton_category_select.setEnabled(True)
        self.ui.pushButton_severity_select.setEnabled(True)

    def __disable_control_panel(self):
        self.ui.pushButton_run.setEnabled(False)
        self.ui.pushButton_stop.setEnabled(False)
        self.ui.pushButton_result.setEnabled(False)
    
    def __enable_control_panel(self):
        self.ui.pushButton_run.setEnabled(True)
        self.ui.pushButton_stop.setEnabled(False)
        self.ui.pushButton_result.setEnabled(True)  
    
    def __enable_menu(self):
        self.enable_menu = True
        self.ui.actionRestart.setEnabled(True)
        self.ui.actionSave.setEnabled(True)
        self.ui.actionClear.setEnabled(True)     
        self.ui.actionSet.setEnabled(True)
        self.ui.actionReset.setEnabled(True)
        self.ui.menuCredential.setEnabled(True)
        self.ui.menuMenu.setEnabled(True)
        
    def __disable_menu(self):
        self.enable_menu = False
        self.ui.actionRestart.setEnabled(False)
        self.ui.actionSave.setEnabled(False)
        self.ui.actionClear.setEnabled(False)
        self.ui.actionSet.setEnabled(False)
        self.ui.actionReset.setEnabled(False)
        self.ui.menuCredential.setEnabled(False)
        self.ui.menuMenu.setEnabled(False)
                      
    def clear_variables(self):
        '''
        clear class variables
        '''
        self.declare_variables()
        
    def print_to_console(self, message):
        curTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        full_message = "[%s] %s" %(curTime, message)
        self.ui.textBrowser_console.append(full_message)
        self.ui.textBrowser_console.moveCursor(QtGui.QTextCursor.End)
        
    def __remove_last_line(self):
        tc = self.ui.textBrowser_console.textCursor()
        tc.movePosition(QtGui.QTextCursor.End)
        tc.select( QTextCursor.LineUnderCursor)
        tc.removeSelectedText()    
        tc.movePosition(QtGui.QTextCursor.StartOfLine)
        tc.movePosition(QtGui.QTextCursor.Up)
        
    def __update_last_line(self, message):
        self.remove_last_line()
        curTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        full_message = "[%s] %s" %(curTime, message)
        self.ui.textBrowser_console.append(full_message)      
    
    def update_last_line(self, message):
        curTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        full_message = "[%s] %s" %(curTime, message)
        self.ui.textBrowser_console.setUndoRedoEnabled(True)
        self.ui.textBrowser_console.undo()
        self.ui.textBrowser_console.append(full_message) 
        self.ui.textBrowser_console.moveCursor(QtGui.QTextCursor.End)
    
    @pyqtSignature("")
    def on_comboBox_project_clicked(self):
        self.__disable_control_panel()
        self.__disable_filter_panel()
        
        if not check_connectivity("http://www.google.com"):
            self.__show_warning_message("The Internet is unreachable. Please check network connection.")
        else:
            if self.mutex.tryLock():
                self.ui.comboBox_project.setEnabled(False)
                if self.personal_key:
                    if check_credential_complete(self.personal_key):
                        self.load_project_list()
                    else:
                        self.__show_warning_message("Invalid credential key. Please set a valid one.")
                else:
                    self.__show_warning_message("No credential key found. Please set one first.")
#                     self.ui.comboBox_project.setEnabled(True)
                    self.mutex.unlock()
        
    def on_select_project(self):            
        if str(self.ui.comboBox_project.currentText()) != self.current_project_name:
            
            self.__disable_preference_panel()
            self.__disable_filter_panel()
            self.__disable_control_panel()
            self.ui.textEdit_lastCopyTime.setEnabled(True)
            
            self.current_project_name = str(self.ui.comboBox_project.currentText())
            
            self.attribute_select_dict.clear()
            
            # Project name
            self.current_project_id = self.ordered_project_dict[self.current_project_name]
            self.print_to_console("Set Project [%s] ID [%s]" %(self.current_project_name,self.current_project_id))            
            
            # Status
            status_dict_random = request_status_dict(self.personal_key)
            self.status_dict = OrderedDict(sorted(status_dict_random.items(), key=lambda t: t[1].upper()))
#             print "status_dict",type(self.status_dict), self.status_dict
            
            # Severity
            self.severity_list = ["S1","S2","S3","S4","S5"]
            
            # Category
            category_dict_random = request_category_dict(self.current_project_id ,self.personal_key)
            if category_dict_random:
                self.category_dict = OrderedDict(sorted(category_dict_random.items(), key=lambda t: t[1].upper()))
#                 print "category_dict",type(self.category_dict), self.category_dict
            else:
                self.category_dict = None
            
            last_cache_time = check_cache(self.current_project_name)
            
            if last_cache_time:
                self.ui.textEdit_lastCopyTime.setText(str(last_cache_time))
                self.ui.checkBox_source.setCheckState(Qt.Unchecked)
                self.ui.checkBox_source.setEnabled(True)
            else:
                self.ui.textEdit_lastCopyTime.setText("N/A")
                self.ui.checkBox_source.setCheckState(Qt.Unchecked)
                self.ui.checkBox_source.setEnabled(False)
            
            self.check_all_filter_set()
            
            if not self.setting_loaded:   # If switch between different projects.
                self.attribute_select_dict.pop("Category_Name", None)
            
#             self.setting_loaded = False
                
#             self.check_all_filter_set()
#             self.check_all_filter_enable()
        else:
            self.print_to_console("Set Project [%s] ID [%s]" %(self.current_project_name,self.current_project_id))
        
        self.ui.pushButton_project_load.setEnabled(True)
        
    def load_project_list(self, block = False):
        if not check_connectivity("http://www.google.com"):
            self.__show_warning_message("The Internet is unreachable. Please check network connection.")
        else:
            self.print_to_console("Project list is loading.")
            
            self.project_loader_inst = Project_Loader.Project_Loader(self.personal_key)
            

            self.project_loader_inst.start()
                
            self.project_loader_inst.load_complete.connect(self.on_load_project_complete)
            self.project_loader_inst.load_fail.connect(self.on_load_fail)
            
    
    @QtCore.pyqtSlot(dict)
    def on_load_project_complete(self, project_dict):    
        self.ordered_project_dict = OrderedDict(sorted(project_dict.items(), key=lambda t: t[0].upper()))
        
        self.ui.comboBox_project.clear()
        self.ui.comboBox_project.addItems(self.ordered_project_dict.keys())
        
        self.print_to_console("Project list loading complete")

#         self.ui.pushButton_project_load.setText("> OK")
        self.ui.comboBox_project.setButtonMode(False)
        self.ui.comboBox_project.setEnabled(True)
        self.loaded = True
        
#         self.check_all_filter_set()
        
        self.mutex.unlock() # release the mutex lock
    
    @QtCore.pyqtSlot()
    def on_load_fail(self): 
        print ">>> on_load_fail"
        
        self.print_to_console("Loading project list from Redmine fails, please try again.")
        self.project_loader_inst.stop()
        self.loaded = False
        self.ui.comboBox_project.setButtonMode(True)
        self.ui.comboBox_project.setEnabled(True)
        self.mutex.unlock() # release the mutex lock
        
    def __show_warning_message(self, message):
        reply = QtGui.QMessageBox.warning(self, 'Warning', message, QtGui.QMessageBox.Yes)
        if reply == QtGui.QMessageBox.Yes:
            print "YES"
    
    def __show_question_message(self, message):
        reply = QtGui.QMessageBox.question(self, 'Question', message, QtGui.QMessageBox.Yes,QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            return True
        if reply == QtGui.QMessageBox.No:
            return False
        
    def __switch_pushButton_project_load(self):
        if self.project_journal_loading:
            self.ui.comboBox_project.setEnabled(True)
            self.ui.pushButton_project_load.setEnabled(True)
            self.project_journal_loading = False
            self.ui.pushButton_project_load.setText("Load")
        else:
            self.ui.comboBox_project.setEnabled(False)
            self.ui.pushButton_project_load.setEnabled(True)
            self.project_journal_loading = True
            self.ui.pushButton_project_load.setText("Stop")
    
    @pyqtSignature("")
    def on_pushButton_project_load_clicked(self):   
        if not self.project_journal_loading:  # For load button
#             self.on_select_project()
            self.__switch_pushButton_project_load()
            self.__disable_loading_panel()
            self.ui.pushButton_project_load.setEnabled(True)
            
            self.start_load_issue_journal()
            
            if not self.setting_loaded:  # Check if it's initial state
                # If switch between different projects.
                self.attribute_select_dict.pop("Category_Name", None)
                
            self.setting_loaded = False
#             self.check_all_filter_set()
            
        else:   # For stop button
            if self.issue_journals_inst:
                if self.__show_question_message("Are you sure you want to terminate the task?"):
                    self.issue_journals_inst.stop() 
    
    def start_load_issue_journal(self):
        self.__disable_preference_panel()
        self.__disable_filter_panel()
        self.__disable_control_panel()
        self.__disable_menu()
        
        MyPrint( self.current_project_name, level='NORMAL')
        
        last_cache_time = check_cache(self.current_project_name)
        
        if last_cache_time:   # check if cache exists for certain project and date
            self.ui.textEdit_lastCopyTime.setText(str(last_cache_time))
            if self.ui.checkBox_source.isChecked(): # if checkbox is checked
                self.print_to_console("Cache created at %s is found, avoid downloading data and load it"%(last_cache_time))
                cache_obj = read_cache(self.current_project_name)
#                 self.ui.checkBox_source.setCheckState(Qt.Checked)
                self.on_send_results(cache_obj)  
                              
            else:   # if checkbox is not checked
                message = "Cache created at %s is found.\nDo you want to load it and skip downloading data from server?"%(last_cache_time)
                
                if self.__show_question_message(message):   # if user select "Yes"
                    self.print_to_console("Cache created at %s is found, avoid downloading data and load it."%(last_cache_time))
                    cache_obj = read_cache(self.current_project_name)
                    self.ui.checkBox_source.setCheckState(Qt.Checked)
                    self.__on_processing_results(cache_obj)
                    
                else:   # if user select "NO"
                    self.print_to_console("Cache created at %s is found, user choose to download newest data."%(last_cache_time))
                    self.ui.checkBox_source.setCheckState(Qt.Unchecked)
                    self.__disable_loading_panel()
                    self.ui.pushButton_project_load.setEnabled(True)
                    self.start_creating_issue_journal()
                    
        else:   # If Cache not found
            self.print_to_console("Cache not found, start loading data.")
            self.ui.textEdit_lastCopyTime.setText("N/A")
            
            if not check_connectivity("http://www.google.com"):
                self.__show_warning_message("The Internet is unreachable. Please check network connection.")
                self.__enable_menu()
            else:
                self.start_creating_issue_journal()
            
    def start_creating_issue_journal(self):     
        self.issue_journals_inst = Issue_Journals_Handler.Create_Issue_Journals(self.current_project_id, self.current_project_name, self.personal_key)
        self.issue_journals_inst.start()
        self.issue_journals_inst.send_results.connect(self.on_send_results) # on_send_complete
        self.issue_journals_inst.send_message.connect(self.on_send_message)
        self.issue_journals_inst.send_stop.connect(self.on_termiate_message)
        self.issue_journals_inst.update_message.connect(self.on_update_message)
        self.issue_journals_inst.load_complete.connect(self.on_journal_load_complate)
    
    @pyqtSignature("")
    def on_pushButton_stop_clicked(self):
        print ">>> on_pushButton_stop_clicked"
        
        if self.issue_journals_inst:
            if self.__show_question_message("Are you sure you want to terminate the task?"):
                self.issue_journals_inst.stop()

    @QtCore.pyqtSlot(str)
    def on_send_results(self, results):
        self.__on_processing_results(results)
    
    @QtCore.pyqtSlot()
    def on_journal_load_complate(self):
        self.__enable_loading_panel()
    
    def __on_processing_results(self, results):
        self.issue_journals_dict = results
        start_date_string = search_start_datetime(self.issue_journals_dict)
        print 'start_date_string -->', start_date_string
        
        today = time.strftime('%Y-%m-%d',time.localtime(time.time()))
        if start_date_string:
            self.ui.dateEdit_start.setDate(QtCore.QDate.fromString(start_date_string,"yyyy-MM-dd"))
        if today:
            self.ui.dateEdit_end.setDate(QtCore.QDate.fromString(today,"yyyy-MM-dd"))
        
        self.__switch_pushButton_project_load()
        self.__enable_preference_panel()
        self.__enable_filter_panel()
        self.__enable_loading_panel()
        self.__enable_menu()
        
        self.mutex.unlock()

    @QtCore.pyqtSlot(str)
    def on_termiate_message(self, message):
        self.issue_journals_inst = None
        self.print_to_console(message)
        #FIX ME
        self.__enable_menu()
        self.__switch_pushButton_project_load()  
        self.__enable_loading_panel()
              
        if check_cache(self.current_project_name):
            self.ui.checkBox_source.setEnabled(True)
        else:
            self.ui.checkBox_source.setEnabled(False)
    
    @pyqtSignature("")
    def on_pushButton_run_clicked(self):
        self.__disable_preference_panel()
        self.__disable_filter_panel()
        self.__disable_control_panel()
        self.__disable_loading_panel()
        self.start_creating_result_date()
        
    def start_creating_result_date(self):
        start_date = self.ui.dateEdit_start.date().toPyDate()
        end_date = self.ui.dateEdit_end.date().toPyDate()
        step_date = int(self.slider_value)
        
        self.issue_journals_inst = Issue_Journals_Handler.Filter_Issue_Journals(self.current_project_id, 
                                                                                self.current_project_name, 
                                                                                start_date, 
                                                                                end_date, 
                                                                                step_date, 
                                                                                self.attribute_select_dict, 
                                                                                self.issue_journals_dict, 
                                                                                self.personal_key
                                                                                )
        self.issue_journals_inst.start()
        self.issue_journals_inst.send_message.connect(self.on_send_message)
        self.issue_journals_inst.update_message.connect(self.on_update_message)
        self.issue_journals_inst.send_stop.connect(self.on_stop_message)
        self.issue_journals_inst.send_complete.connect(self.on_complete_message)
        self.issue_journals_inst.send_result_path.connect(self.on_result_path)
        
    @QtCore.pyqtSlot(str)
    def on_result_path(self, message):
        MyPrint(message, level = "NORMAL")
#         self.print_to_console(message)
        self.last_result_path = message
    
    @QtCore.pyqtSlot(str)
    def on_send_message(self, message):
        MyPrint(message, level = "NORMAL")
        self.print_to_console(message)

    @QtCore.pyqtSlot(str)
    def on_complete_message(self, message):
        MyPrint(message, level = "NORMAL")
        self.print_to_console(message)
        self.__enable_preference_panel()
        self.__enable_filter_panel()
        self.__enable_control_panel()
        self.__enable_loading_panel()
        self.__enable_menu()
          
        last_cache_time = check_cache(self.current_project_name)  
            
        if last_cache_time:
            self.ui.textEdit_lastCopyTime.setText(str(last_cache_time))
            self.ui.checkBox_source.setCheckState(Qt.Unchecked)
            self.ui.checkBox_source.setEnabled(True)
        else:
            self.ui.textEdit_lastCopyTime.setText("N/A")
            self.ui.checkBox_source.setCheckState(Qt.Unchecked)
            self.ui.checkBox_source.setEnabled(False)
        
        self.mutex.unlock()
        
    @QtCore.pyqtSlot(str)
    def on_stop_message(self, message):
        MyPrint(message, level = "NORMAL")
        self.issue_journals_inst = None
        self.print_to_console(message)
        self.__enable_preference_panel()
        self.__enable_filter_panel()
        self.__enable_control_panel()
        self.__enable_menu()
        
        last_cache_time = check_cache(self.current_project_name)  
        
        if last_cache_time:
            self.ui.textEdit_lastCopyTime.setText(str(last_cache_time))
            self.ui.checkBox_source.setCheckState(Qt.Unchecked)
            self.ui.checkBox_source.setEnabled(True)
        else:
            self.ui.textEdit_lastCopyTime.setText("N/A")
            self.ui.checkBox_source.setCheckState(Qt.Unchecked)
            self.ui.checkBox_source.setEnabled(False)

        self.mutex.unlock()
        
    @QtCore.pyqtSlot(str)
    def on_update_message(self, message):
        MyPrint(message, level = "NORMAL")
        self.update_last_line(message)

        
    @pyqtSignature("")
    def on_pushButton_status_select_clicked(self):
        print ">>> on_pushButton_status_select_clicked"
        
        self.status_name_list = self.status_dict.values()
        self.status_id_list = self.status_dict.keys()
#         self.attribute_select_dict.update({"Status_Mapping": self.status_dict})
        attribute_title = "Status"
        attribute_name = "%s_Name" %(attribute_title)
#         print self.attribute_select_dict.keys()
        if attribute_name in self.attribute_select_dict.keys():
            selection_names = self.attribute_select_dict[attribute_name]
        else:
            selection_names = []            
            
        self.show_selection_dialog(attribute_title, 
                                   len(self.status_dict), 
                                   2, 
                                   [self.status_name_list,self.status_id_list], 
                                   selection_names
                                   )
        
    @pyqtSignature("")
    def on_pushButton_category_select_clicked(self):
        print ">>> on_pushButton_category_select_clicked"
        
        self.category_name_list = self.category_dict.values()
        self.category_id_list = self.category_dict.keys()
        attribute_title = "Category"
        attribute_name = "%s_Name" %(attribute_title)

        if attribute_name in self.attribute_select_dict.keys():
            selection_names = self.attribute_select_dict[attribute_name]
        else:
            selection_names = []
            
        self.show_selection_dialog(attribute_title, 
                                   len(self.category_dict), 
                                   2, 
                                   [self.category_name_list,self.category_id_list], 
                                   selection_names
                                   )
 
    @pyqtSignature("")
    def on_pushButton_severity_select_clicked(self):
        print ">>> on_pushButton_severity_select_clicked"
        
        if not self.severity_list:
            return

        attribute_title = "Severity"
        attribute_name = "%s_Name" %(attribute_title)

        if attribute_name in self.attribute_select_dict.keys():
            selection_names = self.attribute_select_dict[attribute_name]
        else:
            selection_names = []
            
        self.show_selection_dialog(attribute_title, len(self.severity_list), 1, [self.severity_list], selection_names)
        

    def show_selection_dialog(self, attribute_title, rows, columns, content_matrix, check_text_list):
        self.attribute_title = "%s" %(attribute_title)
        self.attribute_name = "%s_Name" %(attribute_title)
        self.attribute_id = "%s_ID" %(attribute_title)
        
        self.selection_window = SelectionWindow()
        self.selection_window.accepted.connect(self.on_dialog_accept)
        self.selection_window.reseted.connect(self.on_dialog_reset)
        
        self.selection_window.setup_widget(self.attribute_title, content_matrix, check_text_list )
        self.selection_window.show()
    
    def on_dialog_accept(self):
        selection_names = self.selection_window.select_name_list
        self.attribute_select_dict.update({self.attribute_name: selection_names})
        
        selection_ids  = self.selection_window.select_id_list
        self.attribute_select_dict.update({self.attribute_id: selection_ids})
        
        MyPrint( "%s Name:%s" %( self.attribute_title,selection_names),level = "NORMAL")
        MyPrint( "%s ID  :%s" %( self.attribute_title,selection_ids),  level = "NORMAL")
        
        self.print_to_console("%s:%s" %(self.attribute_title, selection_names))
        self.check_all_filter_set()
#         self.selection_window.clear_wideget()
    
    def on_slider_moved(self):
        self.slider_value = str(self.ui.horizontalSlider_accuracy.value())
        self.ui.label_accuracy.setText(self.slider_value)
        print ">>> Slider Value - ",self.slider_value

    def on_state_changed(self):
        if self.ui.checkBox_source.isChecked():
            self.cache_source = True
        else:
            self.cache_source = False
            
        print ">>> Checkbox Cache Only Value - %s" %(self.cache_source)

    def on_dialog_reset(self):
#         self.selection_names = []
#         self.selection_ids = []
        pass
    
    def check_all_filter_set(self):
        attribute_ready_counter = 0
        
        if self.status_dict:
            if "Status_Name" in self.attribute_select_dict.keys():
                attribute_ready_counter = attribute_ready_counter + 1
                self.ui.pushButton_status_switch.setIcon(QtGui.QIcon(self.icon_check))
            else:
                self.ui.pushButton_status_switch.setIcon(QtGui.QIcon(self.icon_pending))
#             self.ui.pushButton_status_select.setEnabled(True)
        else:
            attribute_ready_counter = attribute_ready_counter + 1
            self.ui.pushButton_status_switch.setIcon(QtGui.QIcon(self.icon_ban))
            self.ui.pushButton_status_select.setEnabled(False)
        
        if self.category_dict:
            if "Category_Name" in self.attribute_select_dict.keys():
                attribute_ready_counter = attribute_ready_counter + 1
                self.ui.pushButton_category_switch.setIcon(QtGui.QIcon(self.icon_check))
            else:
                self.ui.pushButton_category_switch.setIcon(QtGui.QIcon(self.icon_pending))
#             self.ui.pushButton_category_select.setEnabled(True)
        else:
            attribute_ready_counter = attribute_ready_counter + 1
            self.ui.pushButton_category_switch.setIcon(QtGui.QIcon(self.icon_ban))
            self.ui.pushButton_category_select.setEnabled(False)
            
        if self.severity_list:        
            if "Severity_Name" in self.attribute_select_dict.keys():
                attribute_ready_counter = attribute_ready_counter + 1
                self.ui.pushButton_severity_switch.setIcon(QtGui.QIcon(self.icon_check))
            else:
                self.ui.pushButton_severity_switch.setIcon(QtGui.QIcon(self.icon_pending))
#             self.ui.pushButton_severity_select.setEnabled(True)
        else:
            attribute_ready_counter = attribute_ready_counter + 1
            self.ui.pushButton_severity_switch.setIcon(QtGui.QIcon(self.icon_ban))
            self.ui.pushButton_severity_select.setEnabled(False)
            
        if attribute_ready_counter == 3:
            self.__enable_control_panel()

    @pyqtSignature("")
    def on_pushButton_result_clicked(self):
        print "on_pushButton_result_clicked"
#         result_dir = os.path.join(pathProgram(),'Result')
        if self.last_result_path:
            self.print_to_console("Open last result file - %s"%(self.last_result_path))
            
            if os.name == 'nt': # If OS is Windows
                subprocess.Popen('explorer %s' %(self.last_result_path))
            else:   #If OS is other than Windows, linux most likely - posix
                os.system('xdg-open "%s"' %self.last_result_path)
        else:
            self.print_to_console("No record found during the program running.")
        
    @pyqtSignature("")
    def on_actionSave_triggered(self):
#     def on_pushButton_save_clicked(self):
        print "on_pushButton_save_clicked"
        
        if not self.enable_menu:
            self.__show_warning_message("Please manipulate menus when program stops processing data.")
            return 
        
        lines = []
        
        start_date = self.ui.dateEdit_start.date().toPyDate().isoformat()
        end_date = self.ui.dateEdit_end.date().toPyDate().isoformat() 
        accuracy = self.slider_value
        
        lines.append(["project_name", self.current_project_name])
        lines.append(["project_id", self.current_project_id])
        lines.append(["start_date", start_date])
        lines.append(["end_date", end_date])
        lines.append(["accuracy",accuracy])
        
        for key,value in self.attribute_select_dict.iteritems():
            lines.append([key,value]) 

        try:
            saveEnvironment( params = lines)
            
        except Exception,ex:
            print "Error:",ex
            msg = "Saving settings fails"
        else:
            msg = "Save settings successfully"
        finally:
            self.__show_warning_message(msg)

    @pyqtSignature("")
    def on_actionClear_triggered(self):
#     def on_pushButton_clear_clicked(self):
        print "on_pushButton_clear_clicked"
        
        if not self.enable_menu:
            self.__show_warning_message("Please manipulate menus when program stops processing data.")
            return 
        
        message = "The saved settings will be cleared. Are you sure?"
        if self.__show_question_message(message):   # if user select "Yes"
            self.print_to_console("Saved settings have been cleared.")
            cleanEnvironment()
            self.__restart_app()
#             self.ui.pushButton_clear.setEnabled(False)     

    @pyqtSignature("")
    def on_actionRestart_triggered(self):
#     def on_pushButton_restart_clicked(self): 
        if not self.enable_menu:
            self.__show_warning_message("Please manipulate menus when program stops processing data.")
            return 
        
        self.__restart_app()

    @pyqtSignature("")
    def on_actionSet_triggered(self):
        if not self.enable_menu:
            self.__show_warning_message("Please manipulate menus when program stops processing data.")
            return 

        if not check_connectivity("http://www.google.com"):
            self.__show_warning_message("Credential key cannot be verified when Internet is unreachable. Please check network connection.")
        else:
            ready_credential = loadCredential()
            
            if ready_credential:
                self.credential_key = loadCredential()
            else:
                self.credential_key = ""
                
            self.credential_window = CredentialWindow(credential = self.credential_key)
            self.credential_window.show()    
            
            self.credential_window.credential_accpeted.connect(self.on_credential_accpeted)

    @pyqtSignature("")
    def on_actionAbout_triggered(self):
        self.about_window = AboutWindow()
        self.about_window.show()    
    
    @pyqtSignature("")
    def on_actionReset_triggered(self):
        if not self.enable_menu:
            self.__show_warning_message("Please manipulate menus when program stops processing data.")
            return 
        
        if self.__show_question_message("Resetting the credential key will cause the application to restart at meantime. Are you sure?"):
            cleanCredential()
            self.__restart_app()
            
#     def show_credential_dialog(self):
#         if loadCredential():
#             self.credential_key = loadCredential()
#         else:
#             self.credential_key = ""
#             
#         self.credential_window = CredentialWindow(credential = self.credential_key)
#         self.credential_window.show()    
#         
#         self.credential_window.credential_accpeted.connect(self.on_credential_accpeted)
        
    @QtCore.pyqtSlot(str)
    def on_credential_accpeted(self, message): 
        print "Credential - [%s]" %(message)
        self.personal_key = str(message)
        self.credential_window.close()
        saveCredential(self.personal_key)
        self.print_to_console("Credential key is set")
        self.ui.comboBox_project.setEnabled(True)
        self.ui.pushButton_project_load.setEnabled(False)
        
    def __restart_app(self):       
        print "on_pushButton_restart_clicked"
        self.emit(QtCore.SIGNAL("RESTART_REQUEST"), True)

    def __load_settings(self):
        #Try to load environment settings saved before
        param_list = loadEnvironment()
        print param_list
        
        # If environment saved
        if param_list: 
            project_name = param_list[0][1]
            project_id = param_list[1][1]
            start_date = param_list[2][1]
            end_date = param_list[3][1]
            accuracy = param_list[4][1]
            

            if project_name != 'None':
                project_dict = request_project_list(self.personal_key)
                self.ordered_project_dict = OrderedDict(sorted(project_dict.items(), key=lambda t: t[0].upper()))
                project_name_list = self.ordered_project_dict.keys()
                print "project_name", project_name
                print "project_name_list", project_name_list
                project_name_index = project_name_list.index(project_name) + 1
                self.ui.comboBox_project.addItems(project_name_list)
                self.ui.comboBox_project.setCurrentIndex(project_name_index)
                
                self.ui.pushButton_project_load.setEnabled(True)
#                 project_dict = request_project_list(self.personal_key)
#                 self.ordered_project_dict = OrderedDict(sorted(project_dict.items(), key=lambda t: t[0]))
#                 project_name_list = self.ordered_project_dict.keys()
#                 print project_name_list
#                 project_name_index = project_name_list.index(project_name)
#             
#                 self.ui.comboBox_project.addItems(project_name_list)
#                 self.ui.comboBox_project.setCurrentIndex(project_name_index)
            
#                 self.ui.pushButton_project_load.setText("> OK")
                self.ui.comboBox_project.setButtonMode(False)
                self.on_select_project()
                
                
            self.ui.dateEdit_start.setDate(QtCore.QDate.fromString(start_date,"yyyy-MM-dd"))
            self.ui.dateEdit_end.setDate(QtCore.QDate.fromString(end_date,"yyyy-MM-dd"))
             
            self.ui.horizontalSlider_accuracy.setValue(int(accuracy))
            
            if len(param_list) > 5:
                for index in range(5,len(param_list)):
                        self.attribute_select_dict.update({param_list[index][0]:eval(param_list[index][1])}) 
                
                self.loaded = True
                self.check_all_filter_set()
#                 self.__enable_filter_panel()
#                 self.__enable_preference_panel()
                
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MainWindow()
    myapp.show()
    sys.exit(app.exec_())
