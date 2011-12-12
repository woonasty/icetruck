#!/usr/bin/env python

import MySQLdb
import argparse
import sys
import dts
import re
import os
import converter
import datetime
#dt -> date time

dt_pattern = re.compile("(?:^|.*?\D)(\d{1,2}(?::\d{2})+(?:[,.]\d+)?)")

error_words_list = ["Severity", "Fail", "Failed", "ERROR"]

actual_error_logs = []

tp = re.compile("(?:^|.*?\D)(\d{1,2}(?::\d{2})+(?:[,.]\d+)?)")

def lcdUpdater(new_lcd, name):
    print 'updating for instance %s ...to lcd of %s' % (name,new_lcd)
    con  = MySQLdb.connect( host="localhost",
                                user = "root",
                                passwd = "shutup",
                                db = "sqllog")
    cursor = con.cursor()

    sql = "UPDATE icetruck SET `last_checked_date` = '%s' WHERE name = '%s'" %(new_lcd, name)

    try:
        cursor.execute(sql)
        print 'changed lcd'
        cursor.close()
    except:
        print 'Error: unable to fetch data'
        print sys.exc_info()


def emailer(new_lcd, relevant_error_list, name):
    contacts = 'MLBN-DBA@mlb.com'
    print 'starting emailer'
    try:
        len_rel = len(relevant_error_list)
        print 'len(relevant_error_list) --> %s' % (len_rel)   
        
        if len(relevant_error_list) == False:
            print 'nothing to email as final_list_to_mail == False'
        elif len(relevant_error_list) == True:
            final_list_to_mail = ' '.join(relevant_error_list)
        
            doit = '/usr/bin/printf "%s" | /bin/mail -s "%s errorlog notification" %s' % (final_list_to_mail,name,contacts)
            os.system(doit)
    except:
        print 'Error with emailer function'
        print sys.exc_info()   
    lcdUpdater(new_lcd, name)


def errorCatcher(el):
    for word in error_words_list:
        if word in el:
            actual_error_logs.append(el)

def listcatcher(lcd, name):
    std = dts.parseDateTime(lcd)
    print 'std: %s' % (std)
    error_list = []
    error_log_name = 'ERRORLOG.formatted'
    file = directory + error_log_name
    print 'file: %s' % (file)
    opener = open(file, "r")
    print 'opened' 
    for line in opener:
         error_list.append(line) 
    opener.close()
    print 'closed'

    for line in error_list:
        errorCatcher(line)
    print 'finished errorcatcher'
   
    for i,line in enumerate(actual_error_logs):
        dtPart = line[0:22] #slicing line by line for first 22 character 
        if re.match(tp, dtPart): #making sure first 22 characters has a date
            pass
        else:
            print 'popping %s as it does not match the date time in [0:22]' % (i)
            actual_error_logs.pop(i)
    
    relevant_error_logs = [] #list for the actual error logs that meet time requirements

    for i,line in enumerate(actual_error_logs):
        dtPart = line[0:22]
        x = dts.parseDateTime(dtPart) #conversion to a datetime object 
        #print 'last checked date in dateobject form:'
        #print x
        if x <= std:
            print 'log entry(%s) is less than lcd(%s)' % (x,std)
        elif x > std:
            print 'log entry(%s) is GREATER than lcd(%s)' % (x,std)
            print line
            relevant_error_logs.append(line)
    try:
        print 'trying to set new_lcd' 
        if len(relevant_error_logs) == False:
            new_lcd = datetime.datetime.now()
            print 'len(relevant_error_logs==False, setting new_lcd = datetime.datetime.now()'
        elif len(relevant_error_logs) == True: 
            new_lcd = relevant_error_logs[-1][0:22]
            print 'new_lcd set to --> relevant_error_logs[-1][0:22]'
        print 'relevant_error_logs set to --> %s' % (new_lcd)
    except:
        print 'exception hit when trying to set new_lcd'
        print 'this means that there are no indexes in the array(relevant_error_logs'
        print sys.exc_info()
    #needs error checking for formatting 
    print 'this is the new last checked datetime (LCD): %s' % (new_lcd)

    print 'sending to emailer'
    emailer(new_lcd, relevant_error_logs, name)

    
    
def grabber(name):
    go = 1
    print 'grabber started via grabber(%s)' %(name)
    con = MySQLdb.connect (host="localhost",
                            user = "root",
                            passwd = "shutup",
                            db = "sqllog")
    cursor = con.cursor()
   
    sql = "SELECT `last_checked_date` FROM icetruck WHERE `name` = '%s'" % (name)
    
    try:
        cursor.execute(sql)
        row = cursor.fetchone()
        cursor.close()        
        lcd = row[0]
        go = 0
    except:
        print 'Error: unable to fetch data'
        print sys.exc_info()[0]
        go = 1


    if go == 0:
        print lcd
        listcatcher(lcd, name)
    elif go <> 0:
        print 'go <> 0'
    

def actualConversion(name):
    print 'actualConversion name = %s' % (name)
    cmd = 'iconv -f UTF-16 -t UTF-8 %s > %s.formatted' % (fq_el,fq_el)
    try:
        os.system(cmd)
        print 'converted(utf-16 to utf-8) %s ---> %s.formatted \n' % (fq_el,fq_el)
        print 'sending to grabber\n'
        grabber(name)
    except:
        print 'ERROR: unable to fetch data'
        print sys.exc_info()[0]

def checkConversion(name):
    cmd ='file --mime %s' % (fq_el)
    print cmd
    print 'checkConversion name = %s' % (name)
    check = os.popen(cmd)
    holder = check.read()
    if 'utf-16' in holder:
        print 'utf-16 is in this beast'
        print 'sending to conversion function..'
        actualConversion(name)
    else:
        print 'no compatible types'
        print 'exiting'
        sys.exit()



def initProgram(name):
    global conflict_chk
    global directory
    global the_error_log 
    global fq_el 
    the_error_log = 'ERRORLOG'
    directory = '/mnt/dc_sqllog/%s/' % (name)
    semaphore = directory + 'doh'
    file = directory + name
    fq_el = directory + the_error_log
    try:
        if os.path.isfile(semaphore) == True:
            conflict_chk = 1
        elif os.path.isfile(semaphore) == False:
            conflict_chk = 0
        else:
            print 'broken, exiting' #send e-mail with e-mail method
            sys.exit()
    except: 
        print "error: ", sys.exc_info()[0]
        raise

    if conflict_chk == 0:
        print 'No conflict via semaphore file'
        print 'wewt wewt!'
        print 'sending checkConversion(%s)' % (name)
        checkConversion(name)
    else:
        print "There is a conflict via semaphore file existence"
        #possible implementation of a wait(x) and then retry() counter?
        sys.exit()

def arglines():
    parser = argparse.ArgumentParser(description='MLBN ICE TRUCK KILLA', version='1.0alpha')
    parser.add_argument('--name', action='store', dest='name',
                        help='name of the instance to parse')

    args = parser.parse_args()
    print args.name
    initProgram(args.name)
    return


if __name__ == "__main__":
    arglines()
    
