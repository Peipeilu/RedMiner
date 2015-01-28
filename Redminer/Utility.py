import os
import sys
import time
import copy
import urllib2

from datetime import datetime
from PyQt4 import QtGui, QtCore

# Global Variables -------------------------------------------------------------------

#Bigger number means more serious
EventLevel = {'NORMAL':0 ,'DEBUG': 1, 'INFO': 2, 'ERROR': 3, 'FATAL': 4, 'NONE': 5}

# Five levels for log recording
# Level-1:Normal *
# Level-2:DEBUG
# Level-3:INFO
# Level-4:ERROR
# Level-5:FATAL
# Level-6:NONE *
# ALL < DEBUG < INFO < ERROR < FATAL < NONE

MinLevel = 'NORMAL'

# Widgets --------------------------------------------------------------------------
class MyComboBox(QtGui.QComboBox):
    clicked = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super(MyComboBox, self).__init__(parent)
        self.clickable(self).connect(self.onClicked)
        self.buttonMode = True
        
    def onClicked(self):
        print "Combox Box Clicked"
        self.clicked.emit()
    
    def removeClickableEventFilter(self):
        print "Remove Clickable Event Filter"
        self.removeEventFilter(self.clickable_filter)
            
    def clickable(self,widget):
        class Filter(QtCore.QObject):
        
            clicked = QtCore.pyqtSignal()
            
            def eventFilter(self, obj, event):
            
                if obj == widget:
                    if event.type() == QtCore.QEvent.MouseButtonRelease:
                        if obj.rect().contains(event.pos()):
                            self.clicked.emit()
                            # The developer can opt for .emit(obj) to get the object within the slot.
                            return True
                
                return False
        
        self.clickable_filter = Filter(widget)
        widget.installEventFilter(self.clickable_filter)
        return self.clickable_filter.clicked
    
    def setButtonMode(self, flag):
        self.buttonMode = flag
        if flag:
            self.clickable(self).connect(self.onClicked)   
        else:
            self.removeEventFilter(self.clickable_filter)
        
    def mousePressEvent(self,e):
        if self.buttonMode:
            print "Do nothing"    # Do nothing
        else:
            super(MyComboBox, self).mousePressEvent(e)
    
class CheckableTableWidget(QtGui.QWidget):
    """
    Customized Checkable Table Widget
    
    rows (int)
        the number of rows
        
    columns (int)
        the number of columns
        
    content (2-dimension list)
        two-dimension list includes all contents
        example:  [ [1,2,3],    => |1|4|7|
                    [4,5,6],    => |2|5|8|
                    [7,8,9] ]   => |3|6|9|
    
    """
    def __init__(self, parent=None):
        super(CheckableTableWidget, self).__init__(parent)
#         QtGui.QWidget.__init__(parent)
#         self.item_list = [] 
#         self.item_list = [[None]*rows]*columns 
        self.checked_item_name_list = []
        self.checked_item_id_list = []
        self.rows = None
        self.columns = None
        self.item_list = None
        self.checked_texts = []
        
    def setup(self, rows, columns, content, header = []):
        self.rows = rows
        self.columns = columns
        self.content = content
#         self.item_list = [[None]*self.columns]*self.rows 
        self.column_0 = []
        self.column_1 = []
        
        self.table = QtGui.QTableWidget(rows, columns, self)
        
        # Set checkbox for the first row items
        for column in range(self.columns):
            for row in range(self.rows):
                item = QtGui.QTableWidgetItem('%s' % content[column][row])
                
                if column == 0:
                    item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                      QtCore.Qt.ItemIsEnabled)
                    item.setCheckState(QtCore.Qt.Unchecked)
                    self.column_0.append(item)
                else:
                    item.setFlags(QtCore.Qt.ItemIsEnabled)
                    self.column_1.append(item)
        
#                 self.item_list[row][column] = item
#                 print "column[%d],row[%d] = %s" %(column, row, item.text())
                self.table.setItem(row, column, item)

        if header:
            self.table.setHorizontalHeaderLabels(header)
                
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.table)
    
    def setColumnWidth(self, width_list):
        for column in range(len(width_list)):
            self.table.setColumnWidth(column, width_list[column])
    
    def checkItemNameClicked(self):
        for item in self.column_0:
            if item.checkState() == QtCore.Qt.Checked:
#                 print('%s Checked' % item.text()) 
#                 self.checked_item_list.append(item.row())
                self.checked_item_name_list.append(str(item.text()))
        return self.checked_item_name_list

    def checkItemIdClicked(self):
        for i in range(len(self.column_1)):
            item = self.column_0[i]
            if item.checkState() == QtCore.Qt.Checked:
                self.checked_item_id_list.append(str(self.column_1[i].text()))
        return self.checked_item_id_list        

    def clear(self):
        self.checked_item_name_list = []
        self.checked_item_id_list = []
        self.rows = None
        self.columns = None
        self.item_list = None
        self.table.clear()
    
    def reset(self):
        checked_list = []
        for checked_text in self.checked_texts:
            checked_index = self.index_text(checked_text,self.column_0)
            checked_list.append(checked_index)
            self.column_0[checked_index].setCheckState(QtCore.Qt.Checked)
        
        universal_set = set(range(len(self.column_0)))
        unchecked_set = universal_set - set(checked_list)

        for unchecked_index in unchecked_set:
            self.column_0[unchecked_index].setCheckState(QtCore.Qt.Unchecked)
            
    
    def check_texts(self, checked_texts):
        checked_list = []
        self.checked_texts = checked_texts
        for checked_text in checked_texts:
            checked_index = self.index_text(checked_text,self.column_0)
            checked_list.append(checked_index)
            self.column_0[checked_index].setCheckState(QtCore.Qt.Checked)
        
        universal_set = set(range(len(self.column_0)))
        unchecked_set = universal_set - set(checked_list)
        
        for unchecked_index in unchecked_set:
            self.column_0[unchecked_index].setCheckState(QtCore.Qt.Unchecked)
        
    def index_text(self, text, tableItemList):
        for index in range(len(tableItemList)):
            if str(tableItemList[index].text()) == text:
                return index
    
    def yes_to_all(self):
        for item in self.column_0:
            item.setCheckState(QtCore.Qt.Checked)
    
    def no_to_all(self):
        for item in self.column_0:
            item.setCheckState(QtCore.Qt.Unchecked)    
    
# Functions --------------------------------------------------------------------------
def check_connectivity(reference):
    try:
        urllib2.urlopen(reference, timeout=1)
        return True
    except urllib2.URLError:
        return False

def write_cache(content, project_name):
    '''
    Write a cache to temp folder with file name "project name + created time"
    '''
    temp_dir = os.path.join(pathProgram(),'Temp')
    
    if '/' in project_name:
        new_project_name = project_name.replace('/', '-')
    else:
        new_project_name = project_name   

    cur_time = time.strftime('%Y-%m-%d,%H-%M-%S',time.localtime(time.time()))
    file_name = "%s_%s.tmp"%(new_project_name, cur_time)
    cache_path = temp_dir + "\\" + file_name 
    
    MyPrint("Write Cache to path: %s" %(cache_path))
    
    temp_content = copy.deepcopy(content)
    temp_content = encode_datetime(temp_content)
    
    fid = open(cache_path, 'w')
    fid.write('%s'%(temp_content))
    fid.close()
    
    return cache_path

def read_cache(project_name):
    '''
    Read the local data copy based on project name, return a long string
    '''
    temp_dir = os.path.join(pathProgram(),'Temp')
    
    file_list = os.listdir(temp_dir)
    
    for file_name in file_list:
        if project_name in file_name:
            filename_found = file_name
    
    cache_path = temp_dir + "\\" + filename_found 
    
    MyPrint("Read Cache from path: %s" %(cache_path))
    
    fid = open(cache_path, 'r')
    cache_content = fid.read()
    fid.close()
    
    temp_content = eval(cache_content)
    content = decode_datetime(temp_content)
    
    return content

def check_cache(project_name):
    '''
    Check if there is local data copy for a certain project existing.
    '''
    temp_dir = os.path.join(pathProgram(),'Temp')
    
    file_list = os.listdir(temp_dir)
    
    filename_found = False
    
    for file_name in file_list:
        if project_name in file_name:
            filename_found = file_name
    
    if filename_found:
        datetime_str = filename_found.strip('.tmp')
        datetime_str = datetime_str.split('_')[1]
        datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d,%H-%M-%S')
        return datetime_obj
    else:
        return False

def clean_cache(project_name):
    '''
    Remove the local data copy for a certain project.
    '''
    temp_dir = os.path.join(pathProgram(),'Temp')
    
    file_list = os.listdir(temp_dir)
    
    filename_found = False
    
    for file_name in file_list:
        if project_name in file_name:
            filename_found = file_name
            file_full_path = os.path.join(temp_dir,filename_found)
            os.remove(file_full_path)
    
    if filename_found:
        return True
    else:
        return False

##-------- OLD ------------
def read_cache_old(project_name, file_path = None):
    if file_path:
        temp_dir = file_path
    else:
        temp_dir = pathProgram() + '\\Temp'
        
    if '/' in project_name:
        new_project_name = project_name.replace('/', '-')
    else:
        new_project_name = project_name   
    
    cur_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))
    file_name = "%s_%s.tmp"%(new_project_name, cur_time)
    cache_path = temp_dir + "\\" + file_name 
    MyPrint("Read Cache from path: %s" %(cache_path))
    
    fid = open(cache_path, 'r')
    cache_content = fid.read()
    fid.close()
    
    temp_content = eval(cache_content)
    temp_content = decode_datetime(temp_content)
    
    return temp_content

def check_cache_old(project_name, file_path = None):
    if file_path:
        result_dir = file_path
    else:
        result_dir = pathProgram() + '\\Temp'
        
    if '/' in project_name:
        new_project_name = project_name.replace('/', '-')
    else:
        new_project_name = project_name   
    
    cur_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))
    file_name = "%s_%s.tmp"%(new_project_name, cur_time)
    cache_path = result_dir + "\\" + file_name 
    
    if os.path.isfile(cache_path):
        return True
    else:
        return False

def encode_datetime(content):
    for key_issue,value_issue in content.iteritems():
        for key_attribute,value_attribute in value_issue.iteritems():
            for change_list in value_attribute:
                change_list[0] = change_list[0].strftime('%m/%d/%Y_%I:%M:%S')
    return content

def decode_datetime(content):
    for key_issue,value_issue in content.iteritems():
        for key_attribute,value_attribute in value_issue.iteritems():
            for change_list in value_attribute:
#                 change_list[0] = change_list[0].strftime('%m/%d/%Y_%I:%M:%S')
                change_list[0] = datetime.strptime(change_list[0], '%m/%d/%Y_%I:%M:%S')
    return content

def write_csv(content_line_lists, file_name, project_name, file_path = None):
    """
    Write contents to a csv file
    
    content_line_lists (double list)
        list of line element lists
        example: 
        [[1, 2, 3, 4, 5, 6]
         [7, 8, 9,10,11,12]
         ................ ]

    file_name (str)
        the file name of the output csv file
        
    file_path (str)
        the path of the output csv file

    """
    if file_path:
        result_dir = file_path
    else:
        result_dir = pathProgram() + '\\Result'
    
    if '/' in project_name:
        new_project_name = project_name.replace('/', '-')
    else:
        new_project_name = project_name
        
    cur_time = time.strftime('%Y-%m-%d_%H.%M.%S',time.localtime(time.time()))
    file_name = "%s_%s_%s.csv"%(new_project_name, file_name, cur_time)
    result_path = result_dir + "\\" + file_name 
    MyPrint("Write result to path: %s" %(result_path))
    fid = open(result_path, 'w')
    for content_line_list in content_line_lists:
        content_line_str = ','.join(content_line_list)
        fid.write('%s\n'%(content_line_str))
    fid.close()
    
    return result_path
    
def pathProgram():
    """
    Return the working path of the program in string.
    """
    FILEPATH=os.path.abspath(sys.argv[0])
    DIRPATH=os.path.dirname(FILEPATH)
#    ParentPath = os.path.dirname(DIRPATH)
    return str(DIRPATH)

def clean_log():
    logfile = os.path.join(pathProgram(),'Log', 'log.txt')
    fileHandler = open( logfile , 'w' )
    fileHandler.close()

def MyPrint(msg, Verbose=(0,0), level = 'DEBUG'):
    if  EventLevel[level] >= EventLevel[MinLevel]:
        MyPrintf(msg, Verbose, level)

def MyPrintf(msg, Verbose, level):
    """
    Verbose[0] is the level of verbocity requested (e.g., Verbose[0]=None means print nothing, =2 means print messages with <= 2 tabs.
    Verbose[1] is the number of tabs in the prefix: the deeper into function calls you are the more tabs there are.
    """
#     logfile = pathProgram() + '\\Log\\' + 'log.txt'
    logfile = os.path.join(pathProgram(),'Log', 'log.txt')
    
    if not os.path.isfile(logfile):
        fileHandler = open( logfile , 'w' )
        fileHandler.close()
        
    fileHandler = open( logfile , 'a' )

    curTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

    prefix= ''
    line_prefix = ''
    msg = str(msg)
    if msg[0] == '\n':
        msg = msg[1:]
        line_prefix = '\n'
    for i_cnt in range(Verbose[1]):
        prefix += '\x20'*8 #Jeff Mod: Change 1 "tab" to 8 "spaces"
    if Verbose[0] != None and Verbose[0] >= Verbose[1]:
        if level == 'NORMAL':
            prefix_msg =  line_prefix + '[%s][%s]'%(curTime,level) + prefix + msg
        elif level == 'INFO':
            prefix_msg =  line_prefix + '[%s][%s]'%(curTime,level) + prefix + msg
        elif level == 'ERROR':
            prefix_msg =  line_prefix + '[%s][%s]'%(curTime,level) + prefix + msg
        elif level == 'FATAL':
            prefix_msg =  line_prefix + '[%s][%s]'%(curTime,level) + prefix + msg            
        elif level == 'NONE':
            prefix_msg =  line_prefix + '[%s][%s]'%(curTime,level) + prefix + msg                          
        else:
            prefix_msg =  line_prefix + '[%s][%s]'%(curTime,level) + prefix + msg
        print prefix_msg    #Show the log message to command window at front end
        fileHandler.write( prefix_msg + '\n\r' )      #Write the log message to log file at back end
        
    fileHandler.close()   

def is_interger(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def check_settings(file_path = None):
    if file_path:
        full_path = file_path
    else:
        full_path = os.path.join(pathProgram(), "Setting", 'settings.cfg')
    
    if os.path.isfile(full_path):
        return full_path
    else:
        return False

def saveEnvironment(file_path = "",params = []):
    if file_path:
        full_path = file_path
    else:
        full_path = os.path.join(pathProgram(), "Setting", 'settings.cfg')
        
    print "saveEnvironment"
    param_lines = []
#     param_lines.append("Written\n")
    index = 0
    for param in params:
        index = index + 1
        param_line = "%d|%s|%s\n"%(index, param[0],param[1])
        param_lines.append(param_line)
        
    param_lines_chunk = ''.join(param_lines)
    
    fileHandle = open ( full_path, 'w' )
    fileHandle.write( param_lines_chunk )
    fileHandle.close()        
    
def cleanEnvironment(file_path = None):
    if file_path:
        full_path = file_path
    else:
        full_path = os.path.join(pathProgram(), "Setting", 'settings.cfg')
         
    os.remove(full_path)
    
def loadEnvironment(file_path = ""):   #FIX ME
    if file_path:
        full_path = file_path
    else:
        full_path = os.path.join(pathProgram(), "Setting", 'settings.cfg')
    
    param_list = []

    fileHandle = open ( full_path, 'r' )    
    param_line_chunk = fileHandle.read()
#     print "param_line_chunk",param_line_chunk
    
    if not param_line_chunk:
        return False
    
    param_line_list = param_line_chunk.split('\n')
    for param_line in param_line_list:
        if param_line != '' and param_line != None:
            param_element_list = param_line.split('|')
            param_element_list_no_index = param_element_list[1:]
            param_list.append(param_element_list_no_index)
            
    fileHandle.close()
    print param_list
    return param_list

def readVersion(file_path = None):
    if file_path:
        full_path = file_path
    else:
        full_path = os.path.join(pathProgram(), "Setting", "version")
    
    MyPrint("Load Credential from path-%s"%(full_path))
    
    if os.path.isfile(full_path): 
        f = open(full_path,"r")
        personal_key = f.read().strip()
        return personal_key
    else:
        return False
    
def loadCredential(file_path = None):
    if file_path:
        full_path = file_path
    else:
        full_path = os.path.join(pathProgram(), "Setting", "personal_key")
    
    MyPrint("Load Credential from path-%s"%(full_path))
    
    if os.path.isfile(full_path): 
        f = open(full_path,"r")
        personal_key = f.read().strip()
        return personal_key
    else:
        return False

def saveCredential(credential = None, file_path = None):
    if file_path:
        full_path = file_path
    else:
        full_path = os.path.join(pathProgram(), "Setting", "personal_key")

    MyPrint("Save Credential from path-%s"%(full_path))    
    

    f = open(full_path,"w")
    f.write(credential)
    return full_path
 
def cleanCredential(file_path = None):
    if file_path:
        key_path = file_path
    else:
        key_path = os.path.join(pathProgram(), "Setting", "personal_key")   
        
    MyPrint("Clean Credential at path-%s"%(key_path))  
    
    if os.path.isfile(key_path): 
        os.remove(key_path)
        return key_path
    else:
        return False