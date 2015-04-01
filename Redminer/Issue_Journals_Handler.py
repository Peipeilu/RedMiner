import sys
import copy
import time

import PyQt4, PyQt4.QtGui
from PyQt4 import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from datetime import datetime
from datetime import timedelta

from Function import *
from Utility import *

UPDATE_LAST_LINE = True
APPEND_TO_END = False

class Create_Issue_Journals(QtCore.QThread):
    send_message = QtCore.pyqtSignal(str)
    update_message = QtCore.pyqtSignal(str)
    send_stop = QtCore.pyqtSignal(str)
    load_complete = QtCore.pyqtSignal()
    send_results = QtCore.pyqtSignal(dict)
    
    def __init__(self, project_id, project_name, personal_key):
        '''
        project_id (string)
        - ID of project
        
        project_name (string)
        - Name of project
        
        personal_key (string)
        - API access key
        
        '''
        
        QtCore.QThread.__init__(self)
        self.personal_key = personal_key
        self.project_id = project_id
        self.project_name = project_name
        self.total_issue_num = None
        
    def run(self):
        self.send_message.emit("Start loading issue journals")
        
        total_issue_num = request_issue_num(self.project_id, self.personal_key)
        estimate_total_sec = total_issue_num * 1.5
        estimate_min = estimate_total_sec/60
        estimate_hour = 0
        if estimate_min > 60:
            estimate_hour = estimate_min/60
            estimate_min = estimate_min%60
        estimate_sec = estimate_total_sec%60
        
        self.send_message.emit("Total issue number: %d" %(total_issue_num))
        
        self.send_message.emit("Estimate time: %d hours %d mins %d seconds" %(estimate_hour, estimate_min,estimate_sec))
        
        self.send_message.emit("Start requesting issue list")
        
        issue_journals_dict = {}
        issue_list = request_issue_list_for_project(self.project_id, self.personal_key, total_issue_num)#[-10:]
        print "***** issue_list *****\n", issue_list,"\n"
        
        index = 0
        for issue_num in issue_list:
            index = index + 1
            percentage = "{0:.0%}".format(float(index)/total_issue_num)
            
            step_num = 20
            steps_done = int(index*step_num/total_issue_num)
            steps_rest = step_num - steps_done
            progress = "|=" + "="*(steps_done-1) + ">" + " "*steps_rest + "|"
            
            header = "(%d/%d) %s %s" %(index, total_issue_num, percentage, progress)
            
            self.update_message.emit(header)
                
            issue_journals_valid = request_issue_journals(issue_num, self.personal_key)
            
            if issue_journals_valid:
                issue_journals_dict.update({issue_num:issue_journals_valid})
        
        self.send_message.emit("Start caching the result data.")
        
        clean_cache(self.project_name)
        write_cache(issue_journals_dict, self.project_name)
        
        self.send_results.emit(issue_journals_dict)
        self.send_message.emit("Complete!\n"+"-"*18)
        self.load_complete.emit()
        
    def stop(self):
        self.send_stop.emit("Stop by User")
        self.terminate()


class Filter_Issue_Journals(QtCore.QThread):
    send_message = QtCore.pyqtSignal(str)
    update_message = QtCore.pyqtSignal(str)
    send_stop = QtCore.pyqtSignal(str)
    send_complete = QtCore.pyqtSignal(str)
    send_result_path = QtCore.pyqtSignal(str)
    
    def __init__(self, project_id, project_name, start_date, end_date, step_date , attribute_select , issue_journals_dict, personal_key):
        '''
        project_id (string)
        - ID of project
        
        project_name (string)
        - Name of project
        
        start_date (datetime.datetime)
        - start date of the result
        
        end_date (datetime.datetime)
        - end date of the result
        
        step_date (int)
        - Step interval in days
        
        attribute_select (dictionary)
        - A dictionary which has attribute names as keys and candidate lists as values
          Example
          {
                Status_ID:['Assigned', 'Closed', 'Delivered', 'delivered_dev']
                Status_Name:['2', '5', '12', '17', '4', '22', '11', '1', '20']
          }
        
        issue_journals_dict (dictionary)
        - Issue journal detail data
        
        personal_key (string)
        - API access key
        
        '''
        QtCore.QThread.__init__(self)
        self.personal_key = personal_key
        self.project_id = project_id
        self.project_name = project_name
        self.start_date = start_date
        self.end_date = end_date
        self.step_date = step_date
        self.attribute_select = attribute_select
        self.total_issue_num = None
        self.issue_journals_dict = issue_journals_dict
        
    def run(self):
        
        print "*******attribute_select********\n", self.attribute_select,"\n"
        
        self.send_message.emit("Start screening issue journals")
# Date filter  
        numdays = (self.end_date - self.start_date).days
        date_list = [self.start_date + timedelta(days = x) for x in range(0, numdays + 1, self.step_date)]
        
        print "***** date list *****\n", date_list,"\n"
        
# Status filter        
        if 'Status_ID' in self.attribute_select.keys():
            status_id_selection = self.attribute_select['Status_ID']
            status_name_selection = self.attribute_select['Status_Name']
        else:
            status_id_selection = 'INVALID'
            status_name_selection = 'INVALID'
                 
        print "***** status ID selection list *****\n", status_id_selection,"\n" , status_name_selection,"\n"
        
# Severity filter
        if 'Severity_Name' in self.attribute_select.keys():
            severity_name_selection = self.attribute_select['Severity_Name']
        else:
            severity_name_selection = 'INVALID'
            
        print "***** severity selection list *****\n", severity_name_selection,"\n"
        
# Category filter
        
        if 'Category_ID' in self.attribute_select.keys():
            category_id_selection = self.attribute_select['Category_ID']
            category_name_selection = self.attribute_select['Category_Name']
        else:
            category_id_selection = ['INVALID']
            category_name_selection = ['INVALID']
            
        print "***** category selection list *****\n", category_id_selection,"\n", category_name_selection,"\n"

# Tracker filter
        
        if 'Tracker_ID' in self.attribute_select.keys():
            tracker_id_selection = self.attribute_select['Tracker_ID']
            tracker_name_selection = self.attribute_select['Tracker_Name']
        else:
            tracker_id_selection = ['INVALID']
            tracker_name_selection = ['INVALID']
            
        print "***** tracker selection list *****\n", tracker_id_selection,"\n", tracker_name_selection,"\n"        
        
# Generate result
        self.send_message.emit("Start generating severity results")
        time.sleep(0.5)
        
        excel_header_list = ['Date','SUM'] + severity_name_selection
        
        content_lists = []
        content_list = []
        counter = []
#         content_list = [excel_header_list[index] for index in range(len(severity_name_selection)+2)]
        content_lists.append(excel_header_list)
        
        for select_datetime in date_list:
            counter = [0]*7
            debug_list = []
            
            for key,value in self.issue_journals_dict.iteritems():
                issue = key
                
                last_status_id = search_latest_attribute(select_datetime, value['status_changes'])                
                last_severity_name = search_latest_attribute(select_datetime, value['severity_changes'])
                last_category_id = search_latest_attribute(select_datetime, value['category_changes'])
                last_tracker_id = search_latest_attribute(select_datetime, value['tracker_changes'])
                
#                 if issue in [10131, 10123, 10063]:
#                     print "*********[%d]%s|%s|%s" %(issue, last_status_id, last_category_id, last_severity_name)
                    
                if  ('INVALID' not in category_id_selection) and (last_category_id not in category_id_selection):
                    continue

                if last_status_id not in status_id_selection:
                    continue
             
                if last_tracker_id not in tracker_id_selection:
                    continue

                if last_severity_name not in severity_name_selection:
                    continue
                
                # Sum Counter
                counter[0] = counter[0] + 1
    
                if   last_severity_name == "S1":
                    counter[1] = counter[1] + 1
                    
                elif last_severity_name == "S2":
                    counter[2] = counter[2] + 1
                    
                elif last_severity_name == "S3":
                    counter[3] = counter[3] + 1
                    
                elif last_severity_name == "S4":
                    counter[4] = counter[4] + 1
                    
                elif last_severity_name == "S5":                
                    counter[5] = counter[5] + 1

                elif last_severity_name == "Not Defined":   #For Undefined severity
                    counter[6] = counter[6] + 1
                    debug_list.append(issue) # For Debugging
                
                else:
                    print "last_severity_name-->",last_severity_name, type(last_severity_name)
                        
#             print "[%s] | S1:%d | S2:%d | S3:%d | S4:%d | S5:%d | SUM:%d | issues_S5:%s" %(select_datetime, counter[1], counter[2], counter[3], counter[4], counter[5], counter[0] , issues_S5)
#             print "[%s] | S1:%d | S2:%d | S3:%d | S4:%d | S5:%d | SUM:%d | issue_closed:%s" %(select_datetime, counter[1], counter[2], counter[3], counter[4], counter[5], counter[0] , issue_closed)
            print "[%s] | S1:%d | S2:%d | S3:%d | S4:%d | S5:%d | Not Defined:%d | SUM:%d | Not Defined:%s" %(
                  select_datetime, counter[1], counter[2], counter[3], counter[4], counter[5],counter[6], counter[0], debug_list)
             
            content_list = [str(counter[index]) for index in range(len(severity_name_selection) + 1)]
            content_list.insert(0, str(select_datetime))
            
            content_lists.append(content_list)
            
            del content_list
            counter = [0]*6
            
        content_lists.append([])
        
        if status_name_selection: 
            status_list_str = 'Status: '+'|'.join(status_name_selection)
        else:
            status_list_str = 'Status: '+'None'
        
        if category_name_selection:
            category_list_str = 'Category: '+'|'.join(category_name_selection)
        else:
            category_list_str = 'Category: '+'None'
        
        if severity_name_selection:
            severity_list_str = 'Severity: '+'|'.join(severity_name_selection)
        else:
            severity_list_str = 'Severity: '+'None'

        if tracker_name_selection:
            tracker_list_str = 'Tracker: '+'|'.join(tracker_name_selection)
        else:
            tracker_list_str = 'Tracker: '+'None'
            
        print status_list_str
        print severity_list_str
        print tracker_list_str
        print category_list_str
        
        content_lists.append([status_list_str])
        content_lists.append([category_list_str])
        content_lists.append([severity_list_str])
        content_lists.append([tracker_list_str])
            
        result_path = write_csv(content_lists, "SEVERITY", self.project_name)
        self.send_result_path.emit(result_path)
        self.send_message.emit("Generate result to path - %s" %(result_path))
        self.send_complete.emit("Complete!\n"+"-"*18)
                
    def stop(self):
        del self.personal_key
        del self.project_id
        del self.project_name
        del self.start_date
        del self.end_date
        del self.attribute_select
        del self.total_issue_num
        self.send_stop.emit("Stop by User")
        self.terminate()
        