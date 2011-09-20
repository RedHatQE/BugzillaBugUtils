#!/usr/bin/python -tt

from bugzilla.bugzilla3 import Bugzilla36
import  optparse, fileinput
import smtplib
from email.mime.text import MIMEText

parser = optparse.OptionParser()

desc = "gen bugzilla report"

parser.add_option('-u', '--bugzilla_username', type='string', dest='BZUSER', help='bugzilla username')
parser.add_option('-p', '--bugzilla_password', type='string', dest='BZPASS', help='bugzilla password')
parser.add_option('-f', '--product', type='string', dest='PRODUCT', help='bugzilla Product')
parser.add_option('-z', '--emailQA', action='store_true', dest='EMAILQA', help='send email report to QE')
parser.add_option('-y', '--emailDEV', action='store_true', dest='EMAILDEV', help='send email report to DEV')
parser.add_option('-r', '--createReport', action='store_true',dest='REPORT', help='generate a report, no email')

(opts, args) = parser.parse_args()

DEV_STATES='ON_DEV,NEW,ASSIGNED,ON_DEV,MODIFIED,POST'
QA_STATES='ON_QA'


bugzilla = Bugzilla36(url='https://bugzilla.redhat.com/xmlrpc.cgi', user=opts.BZUSER, password=opts.BZPASS)



def email_onqa():
    setOfQA = getSetOfEngineers(QA_STATES)
    print(setOfQA)
    for thisQA in setOfQA:
        bugQuery = {
                               'product': opts.PRODUCT,
                               'bug_status':QA_STATES,
                               'qa_contact': thisQA
                               }
        thisQA_onQA = bugzilla.query(bugQuery)
        email_txt = opts.PRODUCT+' bugs for '+ thisQA+' \n'
        for thisbug in thisQA_onQA:
            bugnum = str(thisbug)[1:7]
            email_txt += (str(thisbug)+'\n https://bugzilla.redhat.com/show_bug.cgi?id='+bugnum+ '\n\n')
        print email_txt
        msg = MIMEText(email_txt)
        msg['Subject'] = opts.PRODUCT+" Bugs"
        s = smtplib.SMTP('localhost')
        s.sendmail(opts.BZUSER, thisQA, msg.as_string())
        s.quit()    
       
def email_ondev():
    setOfDevelopers = getSetOfEngineers(DEV_STATES)
    print(setOfDevelopers)
    for thisDev in setOfDevelopers:
        ondevForThisDevDict = {
                               'product': opts.PRODUCT,
                               'bug_status':DEV_STATES,
                               'assigned_to': thisDev
                               }
        thisdev_ondev = bugzilla.query(ondevForThisDevDict)
        email_txt = opts.PRODUCT+' bugs for '+ thisDev+' \n'
        for thisbug in thisdev_ondev:
            bugnum = str(thisbug)[1:7]
            email_txt += (str(thisbug)+'\n https://bugzilla.redhat.com/show_bug.cgi?id='+bugnum+ '\n\n')
        print email_txt
        msg = MIMEText(email_txt)
        msg['Subject'] = opts.PRODUCT+" Bugs"
        s = smtplib.SMTP('localhost')
        s.sendmail(opts.BZUSER, thisDev, msg.as_string())
        s.quit()

def  getSetOfEngineers(bugStates):
    setOfDevelopers = set([])
    setOfQA = set([])
    bugQuery = {
                        'classification':'Red Hat',
                        'product': opts.PRODUCT,
                        'bug_status':bugStates
                           }
    print('bug query='+str(bugQuery))
    queryResult = bugzilla.query(bugQuery)
    #print(queryResult)
    
    for thisbug in queryResult:
        bugnum = str(thisbug)[1:7]
        mybug = bugzilla.getbug(bugnum)
        if bugStates == DEV_STATES:
            developer = mybug.__getattribute__('assigned_to')
            setOfDevelopers.add(developer)
            #print(developer)
            
        if bugStates == QA_STATES:
            qa = mybug.__getattribute__('qa_contact')
            setOfQA.add(qa)
            #print(qa)
            
    if bugStates == DEV_STATES:
        return setOfDevelopers
    else:
        return setOfQA


        
def createBugReport():
    print('CREATING BUG REPORT')
    setOfQA = getSetOfEngineers(QA_STATES)
    print('set of QA='+str(setOfQA))
    setOfDevelopers = getSetOfEngineers(DEV_STATES)
    print('set of DEV='+str(setOfDevelopers))
    
    reportTxt = ''
    for thisQA in setOfQA:
        bugQueryQA = {
                               'product': opts.PRODUCT,
                               'bug_status':QA_STATES,
                               'qa_contact': thisQA
                               }
        thisQA_onQA = bugzilla.query(bugQueryQA)
        reportTxt += 'QE: '+thisQA+ ' has '+str(len(thisQA_onQA))+ " bugs \n"
        
    for thisDEV in setOfDevelopers:
        bugQueryDEV = {
                               'product': opts.PRODUCT,
                               'bug_status':DEV_STATES,
                               'assigned_to': thisDEV
                               }
        thisDEV_onDEV = bugzilla.query(bugQueryDEV)
        reportTxt += 'DEV: '+thisDEV+ ' has '+str(len(thisDEV_onDEV))+ " bugs \n"
    
    print(reportTxt)
            
        
    

if opts.EMAILQA:
    print('EMAILING QA BUG REPORT')
    email_onqa()

if opts.EMAILDEV:
    print('EMAILING DEV BUG REPORT')
    email_ondev()

if opts.REPORT:
    print('CREATING REPORT')
    createBugReport()
