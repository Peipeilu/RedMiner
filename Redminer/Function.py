# -*- coding: utf-8 -*- 

# The main routine of the program
import sys
import os
import urllib
import xml
import time
from Utility import MyPrint

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
    
from xml.dom import minidom as minidom
from datetime import datetime

def check_credential_sim(credential):
    if len(credential) == 40:
        return True
    else:
        return False    

def check_credential_complete(credential):
    try:
        project_total_num = request_project_num_for_user(credential)
    except:        
        return False
    else:
        return project_total_num
    
def search_start_datetime(issue_journals_dict):
    """
    Return the earliest date of all changes of attributes.
    It may be the starting date of a project as well.
    """
    current_datetime = datetime.now()
    start_datetime = current_datetime
     
    for key,value in issue_journals_dict.iteritems():
        for k,v in value.iteritems():
            first_datetime = v[0][0]
            if first_datetime < start_datetime:
                start_datetime = first_datetime
    
    start_date_string = start_datetime.strftime('%Y-%m-%d')
    
    if start_datetime == current_datetime:
        return False
    else:
        return start_date_string
    
def search_latest_attribute(select_datetime, attribute_change_list):
    """
    Return the latest attribute of issue in the select date and time from the list.
 
    select_datetime (datetime.datetiem)
        the project number 
    
    status_change_list (list)
        status_change_list
        example: (datetime.datetime(2014, 10, 14, 12, 21, 59), 0, 1) or 
                 [datetime.datetime(2014, 10, 14, 12, 21, 59), 0, 1]
    """
    last_status_time = None
    old_status = None
    new_status = None
    
    for status_change_item in attribute_change_list:
        status_change_date = status_change_item[0].date()
#         status_change_date = status_change_item[0]
        if status_change_date < select_datetime:
            last_status_time = status_change_item[0]
            old_status = status_change_item[1]
            new_status = status_change_item[2]
        else:
            break
    
    if new_status:           
        return new_status
    else:
        return False

def build_issue_journals_for_project(project_num, personal_key, total_issue_num = None):
    """
    Scan all issues under a certain project and 
    return a dictionary where issue_num is the key and 
    issue_journals object is the value 
 
    project_num (int)
        the project number 
    
    personal_key (str)
        the user's credential key
    
    """
    issue_journals_dict = {}
    issue_list = request_issue_list_for_project(project_num, personal_key, total_issue_num)#[-1:]

    i = 0
    for issue_num in issue_list:
        i = i + 1
        MyPrint("(%d/%d) Issue %d" %( i, total_issue_num, issue_num), level='DEBUG')

        issue_journals_valid = request_issue_journals(issue_num, personal_key)
        if issue_journals_valid:
            issue_journals_dict.update({issue_num:issue_journals_valid})

    return issue_journals_dict


def __request_issue_list(project_num, offset_num, personal_key):
    request = '/issues.xml?project_id=%s&status_id=*&offset=%s&limit=100' %(project_num, offset_num)
    
    request_url = generate_url(request, personal_key)
    issue_id_list = []

    xml = urllib.urlopen(request_url)  
#         print_dom(minidom.parse(xml))  
    tree = ET.parse(xml) 
    root = tree.getroot()    
    
#     print root.get("total_count")
    
    for issue in root.getiterator('issue'):
        issue_id = int(issue.find('id').text)
        issue_id_list.append(issue_id)
    
    return issue_id_list
        
def request_issue_num(project_num, personal_key):
    request = '/issues.xml?project_id=%s&status_id=*&offset=0&limit=10' %(project_num)
    
    request_url = generate_url(request, personal_key)

    xml = urllib.urlopen(request_url)  
#         print_dom(minidom.parse(xml))  
    tree = ET.parse(xml) 
    root = tree.getroot()    
    
    return int(root.get("total_count"))

def request_issue_list_for_project(project_num, personal_key, total_issue_num):
    """
    Scan all issues under a certain project and return a list of 
    all issue id numbers.
    
    project_num (int)
        the project number 
    
    personal_key (str)
        the user's credential key
    
    """
#     ISSUE_MAXIMAL_NUM = 400
    issue_request_num = 0   
    issue_id_list = []

    try:
        while issue_request_num < total_issue_num:
            issue_list_part = __request_issue_list(project_num, issue_request_num, personal_key)
            issue_id_list.extend(issue_list_part)
            
            issue_request_num = issue_request_num + 100
        
        MyPrint("ISSUE NUM:%d" %(len(issue_id_list)), level="DEBUG")
        return issue_id_list
        
    except Exception,ex:
        print(ex)

def request_issue_journals(issue_num, personal_key):    #FIXME BELOW
    """
    Scan all issue journals by its issue num. 
    Return a tuple 
        {"status_changes":status_changes, "severity_changes":severity_changes, "priority_changes":priority_changes}, where 
                status_changes   (list) = [created_time, old_value_status, new_value_status]
                severity_changes (list) = [created_time, old_value_severity, new_value_severity]
                priority_changes (list) = [created_time, old_value_priority, new_value_priority]
    
    project_num (int)
        the project number 
    
    personal_key (str)
        the user's credential key
    
    *acceleration <optional> (bool) 
        speed up the scan process obviously but may bring risks in
    
    """
    request = '/issues/%s.xml?include=journals' %(issue_num)
    request_url = generate_url(request, personal_key)
    
    status_changes = []
    severity_changes = []
    priority_changes = []
    category_changes = []
    
    journal_change = {}
    
    severity_scan = True
    priority_scan = True
    status_scan = True
    category_scan = True
    
    old_value_status = ""
    new_value_status = ""
    old_value_severity = ""
    new_value_severity = ""
    old_value_priority = ""
    new_value_priority = ""
    
    first_severity_change_flag = True
    first_status_change_flag   = True
    first_priority_change_flag = True
    first_category_change_flag = True
    
    first_value_status = ""
    first_value_severity = ""
    first_value_priority = ""
    first_value_category = ""
    
    xml = urllib.urlopen(request_url)
#     print_dom(minidom.parse(xml))
    
    tree = ET.parse(xml) 
    root = tree.getroot()
    
    severity_current = 'Not Defined'
    priority_current = 'Not Defined'
    status_current   = 'Not Defined'
    category_current = 'Not Defined'
    
    for custom_field in root.getiterator('custom_field'):  
            if custom_field.get('name') == "Seagate Severity" or custom_field.get('id') == "65":
                severity_current = custom_field.find('value').text

            if custom_field.get('name') == "Seagate Priority" or custom_field.get('id') == "64":
                priority_current = custom_field.find('value').text
    
    if root.find('status') != None:
        status_current = root.find('status').get('id')  # Status ID number
    
    if root.find('category') != None:
        category_current = root.find('category').get('id')  # Category ID number
    
# PRESCAN THE HEADER TO IGNORE USELESS WORK - START
    # check if value is "Not Defined" or blank character
    if status_current is "Not Defined" or not status_current: # Skip scanning detail if current status is "Not Defined" OR ""
        status_scan = False
        first_value_status = "Not Defined"
    else:
        first_value_status = status_current
    
    if severity_current is "Not Defined" or not severity_current:  # Skip scanning detail if current value is  "Not Defined" OR ""
        severity_scan = False
        first_value_severity = "Not Defined"
    else:
        first_value_severity = severity_current
    
    if priority_current is "Not Defined" or not priority_current:  # Skip scanning detail if current value is  "Not Defined" OR ""
        priority_scan = False
        first_value_priority = "Not Defined"
    else:
        first_value_priority = priority_current
    
    if category_current is "Not Defined" or not category_current:
        category_scan = False
        first_value_category = "Not Defined"
    else:
        first_value_category = category_current

# PRESCAN THE HEADER TO IGNORE USELESS WORK - END
    for journal in root.getiterator('journal'):
        created_on = journal.find('created_on').text
        created_time = datetime.strptime(created_on, '%Y-%m-%dT%H:%M:%SZ') 
        
        details = journal.find('details') 
         
        for detail in details.findall('detail'):
            if status_scan and detail.get('name') == "status_id":   # status change
                # Return Time Information Sample: 2014-10-22T22:36:40Z
                old_value_status = detail.find('old_value').text if detail.find('old_value').text else "Not Defined"
                new_value_status = detail.find('new_value').text if detail.find('new_value').text else "Not Defined"
                   
                status_changes.append([created_time,old_value_status,new_value_status])

                if first_status_change_flag:
                    first_value_status = old_value_status
                    first_status_change_flag = False
                
                MyPrint( "(%s) Status | old -> new : %s -> %s" %(created_time, old_value_status, new_value_status),level='DEBUG')
            
            elif severity_scan and detail.get('name') == "65":    # severity change   
                old_value_severity = detail.find('old_value').text if detail.find('old_value').text else "Not Defined"
                new_value_severity = detail.find('new_value').text if detail.find('new_value').text else "Not Defined"
                
                severity_changes.append([created_time,old_value_severity,new_value_severity])     
                
                if first_severity_change_flag:
                    first_value_severity = old_value_severity
                    first_severity_change_flag = False
                
                MyPrint( "(%s) Severity | old -> new : %s -> %s" %(created_time, old_value_severity, new_value_severity),level='DEBUG')
            
            elif priority_scan and detail.get('name') == "64":    # priority change

                old_value_priority = detail.find('old_value').text if detail.find('old_value').text else "Not Defined"
                new_value_priority = detail.find('new_value').text if detail.find('new_value').text else "Not Defined"
                
                priority_changes.append([created_time,old_value_priority,new_value_priority])                 
                
                if first_priority_change_flag:
                    first_value_priority = old_value_priority
                    first_priority_change_flag = False
                    
                MyPrint( "(%s) Priority | old -> new : %s -> %s" %(created_time, old_value_priority, new_value_priority), level='DEBUG')
            
            elif category_scan and detail.get('name') == "category_id":
                
                old_value_category = detail.find('old_value').text if detail.find('old_value').text else "Not Defined"
                new_value_category = detail.find('new_value').text if detail.find('new_value').text else "Not Defined"

                category_changes.append([created_time,old_value_category,new_value_category])      
                
                if first_category_change_flag:
                    first_category_change_flag = False
                    first_value_category = old_value_category
                    
                MyPrint( "(%s) Category | old -> new : %s -> %s" %(created_time, old_value_category, new_value_category), level='DEBUG')
                   
# ADD IN INITIAL ISSUE ATTRIBUTES - START
    created_on = root.find('created_on').text
    created_time = datetime.strptime(created_on, '%Y-%m-%dT%H:%M:%SZ') 
    
    old_value_status = "Not Defined"    # State - Not Defined
    new_value_status = first_value_status    # State - New
    
    status_changes.insert(0, [created_time,old_value_status,new_value_status])
    
    MyPrint( "(%s) Status | old -> new : %s -> %s" %(created_time, old_value_status, new_value_status), level='DEBUG')
    
    old_value_severity = "Not Defined"
    new_value_severity = first_value_severity
    
    severity_changes.insert(0, [created_time,old_value_severity,new_value_severity])     
    
    MyPrint( "(%s) Severity | old -> new : %s -> %s" %(created_time, old_value_severity, new_value_severity), level='DEBUG')
    
    old_value_priority = "Not Defined"
    new_value_priority = first_value_priority
    
    priority_changes.insert(0, [created_time,old_value_priority,new_value_priority]) 
    
    MyPrint( "(%s) Priority | old -> new : %s -> %s" %(created_time, old_value_priority, new_value_priority), level='DEBUG')
    
    old_value_category = "Not Defined"
    new_value_category = first_value_category
    
    category_changes.insert(0, [created_time,old_value_category,new_value_category])
    
    MyPrint( "(%s) Category | old -> new : %s -> %s" %(created_time, old_value_category, new_value_category), level='DEBUG')
      
# ADD IN INITIAL ISSUE ATTRIBUTES - END

    journal_change = {"status_changes":status_changes, "severity_changes": severity_changes, 
                      "priority_changes":priority_changes, "category_changes": category_changes }
    
    print "-----------------------------"    
    
    return journal_change

def __request_issue_status_journals(issue_num, personal_key):
    """
    Scan journals of a certain issue by its issue number and 
    return a list containing a sequence of tuples. Each tuple
    record the time, old status and new status for every changing 
    of status.
 
    issue_num (int)
        the project number 
    
    personal_key (str)
        the user's credential key
    
    """
    
    request = '/issues/%s.xml?include=journals' %(issue_num)
    request_url = generate_url(request, personal_key)
    status_journal = []
    
    try:
        xml = urllib.urlopen(request_url)
#         print_dom(minidom.parse(xml))

        tree = ET.parse(xml) 
        root = tree.getroot()
        
        for issue in root.getiterator('issue'):
            created_on = issue.find('created_on').text
            created_time = datetime.strptime(created_on, '%Y-%m-%dT%H:%M:%SZ') 
            old_value = 0
            new_value = 1
            
            status_journal.append((created_time,old_value,new_value))
            
            print "[%s] old status -> new_status : %s -> %s" %(created_time, old_value,new_value)
            
        for journal in root.getiterator('journal'):
            created_on = journal.find('created_on').text
            details = journal.find('details') 
             
            for detail in details.findall('detail'):
                if detail.get('name') == "status_id":
                    # Return Time Information Sample: 2014-10-22T22:36:40Z
                    created_time = datetime.strptime(created_on, '%Y-%m-%dT%H:%M:%SZ') 
                    old_value = int(detail.find('old_value').text)
                    new_value = int(detail.find('new_value').text)
                       
                    status_journal.append((created_time,old_value,new_value))
                    
                    print "[%s] old status -> new_status : %s -> %s" %(created_time, old_value,new_value)
        
        print "-----------------------------"    
        return status_journal

    except Exception,ex:
        print "ERROR:",ex

def print_dom(dom_object):
    pretty_xml_as_string = dom_object.toprettyxml()
    print "-----------------------------"
    print pretty_xml_as_string
    print "-----------------------------"

def generate_url(request, personal_key):
    """
    Return the complete url for different request.
 
    request (str)
        the core short request path (ignore the website prefix and key attribute postfix) 
    
    personal_key (str)
        the user's credential key
    
    """
    
    if '?' in request:
        # if question mark already exist in short request
        request_url = 'http://redminesbs.plan.io' + request + '&key=' + personal_key
    else:
        request_url = 'http://redminesbs.plan.io' + request + '?key=' + personal_key
    
    print request_url
    
    return request_url
    
def request_project_num_for_user(personal_key):
    """
    NEW
    
    Return the total number of project which can
    be accessed by user
    
    PARAMETER DEFINITION
    
    personal_key (str)
    the user's credential key
    
    RETURN FORMAT (str)
    the total number of project
    
    """
    request = '/projects.xml?limit=1'
    request_url = generate_url(request, personal_key)
    xml = urllib.urlopen(request_url)
#         print_dom(minidom.parse(xml))
    tree = ET.parse(xml) 
    root = tree.getroot()       
    attrib_dict = root.attrib
    
    return str(attrib_dict['total_count'])

def request_project_dict_for_user(personal_key, total_project_num = None):
    """
    NEW
    
    Scan all issues can be accessed by a certain API Key 
    and return a list of all project numbers 
 
    personal_key (str)
        the user's credential key
    
    optional - total_project_num (str)
        total project number to be manually set
    
    """
    request_project_num = 0   
    project_dict = {}    
    
    if not total_project_num:
        total_project_num = request_project_num_for_user(personal_key)
        
    total_project_num = int(total_project_num)
    MyPrint( "--> Total Project Number: %d" %(total_project_num), level='NORMAL')
    
    while request_project_num < total_project_num:
        project_list_part = request_project_list(request_project_num, personal_key)
        project_dict.update(project_list_part)
        request_project_num = request_project_num + 100
        
    return project_dict
 
def request_project_list(offset_num, personal_key):
    """
    UPDATE
    
    Return the dictionary that can be accessed by a certain credential key. 
    Key is the project name and value is the project number.
 
    offset_num (str)
        starting point offset number
    
    personal_key (str)
        the user's credential key
    
    """
    request = '/projects.xml?offset=%s&limit=100' %(offset_num)
    request_url = generate_url(request, personal_key)    
    
    project_name_id_dict = {}
    
    xml = urllib.urlopen(request_url)
#         print_dom(minidom.parse(xml))
    tree = ET.parse(xml) 
    root = tree.getroot()
    
    for project in root.getiterator('project'):
        project_id = project.find('id').text
        project_name = project.find('name').text
        project_name_id_dict.update({project_name:project_id})
        
    return project_name_id_dict
    
def request_status_dict(personal_key):
    """
    Return the project status list on Redmine.

    personal_key (str)
        the user's credential key
    
    """
    
    request = '/issue_statuses.xml'
    request_url = generate_url(request, personal_key)
    status_id_dict = {}
    
    try:
        xml = urllib.urlopen(request_url)
#         print_dom(minidom.parse(xml))
        
        tree = ET.parse(xml) 
        root = tree.getroot()
        
        for issue_status in root.getiterator('issue_status'): 
            status_id = issue_status.find("id").text
            status_name = issue_status.find("name").text 
            status_id_dict.update({status_id:status_name})

        return status_id_dict             
                
    except Exception,ex:
        print(ex)   

def request_category_dict(project_id, personal_key):
    """
    Return the category list in a certain project.

    project_id (str)
        the project id number
    
    personal_key (str)
        the user's credential key
    
    """
    
    request = '/projects/%s/issue_categories.xml' %(project_id)
    request_url = generate_url(request, personal_key)
    category_id_dict = {}
    
    try:
        xml = urllib.urlopen(request_url)
#         print_dom(minidom.parse(xml))
        
        tree = ET.parse(xml) 
        root = tree.getroot()
        
        for issue_status in root.getiterator('issue_category'): 
            category_id = issue_status.find("id").text
            category_name = issue_status.find("name").text 
            category_id_dict.update({category_id:category_name})

        return category_id_dict             
                
    except Exception,ex:
        print(ex) 


# Old Implementation ----------------------------------

def __old_request_issue_journals(issue_num, personal_key):  # minidom implementation
    request = '/issues/%s.xml?include=journals' %(issue_num)
    request_url = generate_url(request, personal_key)
    
    try:
        xml = urllib.urlopen(request_url)

        tree= ET.parse(xml) 
        root = tree.getroot()
        
        detail_nodes = root.getiterator("detail")
        for detail_node in detail_nodes:
            if detail_node.attrib['name'] == "status_id":
                print "old status -> new_status %s -> %s" %(detail_node.getchildren()[0].text,detail_node.getchildren()[1].text)
        print root['issue']
     
    except Exception,ex:
        print(ex)

def __old_request_project_list(request, personal_key):  # minidom implementation
    project_name_id_dict = {}
    
    request_url = generate_url(request, personal_key)
    
    try:
        xml = urllib.urlopen(request_url)
        dom = minidom.parse(xml)
        root = dom.documentElement
        names = root.getElementsByTagName("name")
        ids = root.getElementsByTagName("id")
  
        for index in range(0,len(names)): 
            project_name = names[index].firstChild.data
            project_id = int(ids[index].firstChild.data)
            project_name_id_dict.update({project_name:project_id})
            
#         return project_names
        return project_name_id_dict
        
    except Exception,ex:
        print(ex)

def __old_request_status_dict(personal_key):    # minidom implementation
    request = '/issue_statuses.xml'
    request_url = generate_url(request, personal_key)
    
    status_id_dict = {}
    
    try:
        xml = urllib.urlopen(request_url)
        dom = minidom.parse(xml)        
        root = dom.documentElement
        names = root.getElementsByTagName("name")
        ids = root.getElementsByTagName("id")
        
        for index in range(0,len(names)): 
            issue_name = names[index].firstChild.data
            issue_id = int(ids[index].firstChild.data)

            status_id_dict.update({issue_id:issue_name})
            
#         return project_names
        return status_id_dict             
                
    except Exception,ex:
        print(ex)   

def __old_request_issue_list_for_project(project_num, personal_key):
    """
    Scan all issues under a certain project and return a list of 
    all issue id numbers.
    
    project_num (int)
        the project number 
    
    personal_key (str)
        the user's credential key
    
    """
#     request = '/issues.xml?project_id=%s&offset=0&limit=100' %(project_num)
    request = '/issues.xml?project_id=%s&status_id=*&offset=0&limit=101' %(project_num)
            
    request_url = generate_url(request, personal_key)
    issue_id_list = []
    try:
        xml = urllib.urlopen(request_url)    
        tree = ET.parse(xml) 
        root = tree.getroot()    
        
        for issue in root.getiterator('issue'):
            issue_id = int(issue.find('id').text)
            issue_id_list.append(issue_id)
        
        return issue_id_list
        
    except Exception,ex:
        print(ex)


if __name__ == '__main__':
    API_Key = '92a0618f19ec413438e4b5b3a3847ce1cd88c67a'
#     __request_issue_list(project_num=292 , offset_num=100, personal_key="92a0618f19ec413438e4b5b3a3847ce1cd88c67a" )
#     print build_issue_journals_for_project(292, "92a0618f19ec413438e4b5b3a3847ce1cd88c67a",300)
#     print request_category_dict(291, "92a0618f19ec413438e4b5b3a3847ce1cd88c67a")
    print request_issue_journals(31111, "92a0618f19ec413438e4b5b3a3847ce1cd88c67a")
    
    
#     issue_travel_dict = {
#                          21717:{
#                                 'severity_changes': [['12/11/2013_02:32:36', 'Not Defined', 'S3']], 
#                                 'status_changes': [['12/11/2013_02:32:36', 'Not Defined', '2']], 
#                                 'priority_changes': [['12/11/2013_02:32:36', 'Not Defined', 'P1']], 
#                                 'category_changes': [['12/11/2013_02:32:36', 'Not Defined', '352'], 
#                                                      ['10/02/2014_10:03:29', '352', '435'], 
#                                                      ['10/03/2014_10:15:14', '435', 'Not Defined'], 
#                                                      ['10/30/2014_10:10:47', 'Not Defined', '423']]
#                                 },
#                          }
#          
#     from Utility import *
#     
#     new_issue_travel_dict = decode_datetime(issue_travel_dict)
#     
#     select_datetime = datetime.strptime('12 30 2013', '%m %d %Y')
#     print 'select_datetime', type(select_datetime)
#     
#     for key,value in new_issue_travel_dict[21717].iteritems():
#         print search_latest_attribute(select_datetime, value)
        
#     request_project_dict_for_user(API_Key, 210)