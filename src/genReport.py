#!/usr/bin/python -tt

from bugzilla.bugzilla3 import Bugzilla36
import  optparse, fileinput
import smtplib
from email.mime.text import MIMEText

parser = optparse.OptionParser()

desc = "gen bugzilla report"

parser.add_option('-u', '--bugzilla_username', type='string', dest='BZUSER', help='bugzilla username')
parser.add_option('-p', '--bugzilla_password', type='string', dest='BZPASS', help='bugzilla password')
parser.add_option('-c', '--classification', type='string', dest='CLASSIFICATION', help='bugzilla Classification: "Red Hat","Fedora","Community","Other",etc')
parser.add_option('-t', '--component', type='string', dest='COMPONENT', help='bugzilla Component')
parser.add_option('-f', '--product', type='string', dest='PRODUCT', help='bugzilla Product')
parser.add_option('-s', '--release', type='string', dest='RELEASE', help='bugzilla Release')
parser.add_option('-z', '--emailQA', action='store_true', dest='EMAILQA', help='send email report to QE')
parser.add_option('-y', '--emailDEV', action='store_true', dest='EMAILDEV', help='send email report to DEV')
parser.add_option('-x', '--emailREPORT', type='string', dest='EMAILREPORT', help='send summary email to provided list of addresses')
parser.add_option('-m', '--modified', action='store_true', dest='MODIFIED', help='list modified bugs in the report')
parser.add_option('-r', '--createReport', action='store_true',dest='REPORT', help='generate a report, no email')

(opts, args) = parser.parse_args()

DEV_STATES='ON_DEV,NEW,ASSIGNED,ON_DEV,MODIFIED,POST'
QA_STATES='ON_QA'
MODIFIED_STATE='MODIFIED' #scratching my own itch here.. looking for bugs to go to the build

if opts.PRODUCT == None or opts.CLASSIFICATION == None:
    print('Please provide a -f bugzilla product and -c bugzilla classification')
    parser.print_help()
    exit(-1)

bugzilla = Bugzilla36(url='https://bugzilla.redhat.com/xmlrpc.cgi', user=opts.BZUSER, password=opts.BZPASS)




def email_onqa():
    setOfQA = getSetOfEngineers(QA_STATES)
    print(setOfQA)
    for thisQA in setOfQA:
        bugQuery = {
                               'classification': opts.CLASSIFICATION,
                               'component': opts.COMPONENT,
                               'product': opts.PRODUCT,
                               'target_release': opts.RELEASE,
                               'bug_status':QA_STATES,
                               'qa_contact': thisQA
                              }
        if opts.COMPONENT == None:
            del bugQuery['component']
        if opts.RELEASE == None:
            del bugQuery['target_release']
        thisQA_onQA = bugzilla.query(bugQuery)
        email_txt = opts.PRODUCT+' bugs for '+ thisQA+' \n'
        for thisbug in thisQA_onQA:
            bugnum = str(thisbug)[1:7]
            email_txt += (str(thisbug)+'\n https://bugzilla.redhat.com/show_bug.cgi?id='+bugnum+ '\n\n')
        #print email_txt
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
                               'classification': opts.CLASSIFICATION,
                               'component': opts.COMPONENT,
                               'product': opts.PRODUCT,
                               'target_release': opts.RELEASE,
                               'bug_status':DEV_STATES,
                               'assigned_to': thisDev
                               }
        if opts.COMPONENT == None:
            del ondevForThisDevDict['component']
        if opts.RELEASE == None:
            del ondevForThisDevDict['target_release']
        thisdev_ondev = bugzilla.query(ondevForThisDevDict)
        email_txt = opts.PRODUCT+' bugs for '+ thisDev+' \n'
        for thisbug in thisdev_ondev:
            bugnum = str(thisbug)[1:7]
            email_txt += (str(thisbug)+'\n https://bugzilla.redhat.com/show_bug.cgi?id='+bugnum+ '\n\n')
        #print email_txt
        buffer = ('############## CRITERIA  ################\n')
        buffer += ('Classification: ') + opts.CLASSIFICATION + '\n'
        buffer += ('Product: ') + opts.PRODUCT + '\n'
        if opts.COMPONENT:
            buffer += ('Component: ') + opts.COMPONENT + '\n'
        if opts.RELEASE:
            buffer += ('Release: ') + opts.RELEASE + '\n'
        buffer += ('#########################################\n\n')
        buffer += email_txt
        print buffer
#        msg = MIMEText(buffert)
#        msg['Subject'] = opts.PRODUCT+" Bugs"
#        s = smtplib.SMTP('localhost')
#        s.sendmail(opts.BZUSER, thisDev, msg.as_string())
#        s.quit()


def email_report():
        # Open provided email addresses file and read in addresses
    files = open(opts.EMAILREPORT, 'r')
    addresses = [x.strip() for x in files.readlines()]

    # Get Report
    report = createBugReport()

    for address in addresses:
        msg = MIMEText(report)
        msg['Subject'] = opts.PRODUCT+" Bugs - Summary Report"
        s = smtplib.SMTP('localhost')
        s.sendmail(opts.BZUSER, address, msg.as_string())
        s.quit()



def  getSetOfEngineers(bugStates):
    setOfDevelopers = set([])
    setOfQA = set([])
    bugQuery = {
                        'classification': opts.CLASSIFICATION,
                        'component': opts.COMPONENT,
                        'product': opts.PRODUCT,
                        'target_release': opts.RELEASE,
                        'bug_status':bugStates
                           }
    if opts.COMPONENT == None:
        del bugQuery['component']
    if opts.RELEASE == None:
        del bugQuery['target_release']
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
    print('CREATING BUG REPORT\n')
    buffer = ""

    totalONQA = bugzilla.query(totalQAQuery)
    totalONDEV = bugzilla.query(totalDEVQuery)
    qaCount = len(totalONQA)
    devCount = len(totalONDEV)

    buffer += ('############## CRITERIA  ################\n')
    buffer += ('Classification: ') + opts.CLASSIFICATION + '\n'
    buffer += ('Product: ') + opts.PRODUCT + '\n'
    if opts.COMPONENT:
        buffer += ('Component: ') + opts.COMPONENT + '\n'
    if opts.RELEASE:
        buffer += ('Release: ') + opts.RELEASE + '\n'
    buffer += ('#########################################\n\n')

    buffer += ('############## BUG COUNTS ###############\n')
    buffer += ('Total bugs ON_QA ='+ str(qaCount)) + '\n'
    buffer += ('Total bugs ON_DEV ='+ str(devCount)) + '\n'
    buffer += ('#########################################\n\n')

    if opts.MODIFIED:
        # bugs that may be ready for QE, but were not flipped to on_qa
        buffer += ('######## Bugs in MODIFIED state #########\n')
        bugsOnModified = bugzilla.query(totalModified)
        for thisbug in bugsOnModified:
            print(thisbug)
            buffer += str(thisbug) + '\n'
        buffer += ('#########################################\n\n')

    setOfQA = getSetOfEngineers(QA_STATES)
    setOfDevelopers = getSetOfEngineers(DEV_STATES)

    for thisQA in setOfQA:
        bugQueryQA = {
                              'classification': opts.CLASSIFICATION,
                              'component': opts.COMPONENT,
                              'product': opts.PRODUCT,
                              'target_release': opts.RELEASE,
                              'bug_status':QA_STATES,
                              'qa_contact': thisQA
                              }
        if opts.COMPONENT == None:
            del bugQueryQA['component']
        if opts.RELEASE == None:
            del bugQueryQA['target_release']

        thisQA_onQA = bugzilla.query(bugQueryQA)
        buffer += 'QE: '+thisQA+ ' has '+str(len(thisQA_onQA))+ " bugs \n"

    for thisDEV in setOfDevelopers:
        bugQueryDEV = {
                              'classification': opts.CLASSIFICATION,
                              'component': opts.COMPONENT,
                              'product': opts.PRODUCT,
                              'target_release': opts.RELEASE,
                              'bug_status':DEV_STATES,
                              'assigned_to': thisDEV
                              }
        if opts.COMPONENT == None:
            del bugQueryDEV['component']
        if opts.RELEASE == None:
            del bugQueryDEV['target_release']

        thisDEV_onDEV = bugzilla.query(bugQueryDEV)
        buffer  += 'DEV: '+thisDEV+ ' has '+str(len(thisDEV_onDEV))+ " bugs \n"

    return buffer


#### VARIOUS PUBLIC QUERIES ################
totalQAQuery = {
                               'classification': opts.CLASSIFICATION,
                               'component': opts.COMPONENT,
                               'product': opts.PRODUCT,
                               'target_release': opts.RELEASE,
                               'bug_status':QA_STATES
                               }
totalDEVQuery = {
                               'classification': opts.CLASSIFICATION,
                               'component': opts.COMPONENT,
                               'product': opts.PRODUCT,
                               'target_release': opts.RELEASE,
                               'bug_status':DEV_STATES
                               }
totalModified = {
                               'classification': opts.CLASSIFICATION,
                               'component': opts.COMPONENT,
                               'product': opts.PRODUCT,
                               'target_release': opts.RELEASE,
                               'bug_status':MODIFIED_STATE
                               }
if opts.COMPONENT == None:
    del totalQAQuery['component']
    del totalDEVQuery['component']
    del totalModified['component']

if opts.RELEASE == None:
    del totalQAQuery['target_release']
    del totalDEVQuery['target_release']
    del totalModified['target_release']

#### VARIOUS PUBLIC QUERIES ################


if opts.EMAILQA:
    print('EMAILING QA BUG REPORT')
    email_onqa()

if opts.EMAILDEV:
    print('EMAILING DEV BUG REPORT')
    email_ondev()

if opts.EMAILREPORT:
    print('EMAILING SUMMARY REPORT')
    email_report()

if opts.REPORT:
    print createBugReport()

if not opts.REPORT and not opts.EMAILDEV and not opts.EMAILQA and not opts.EMAILREPORT:
    print('NOOP. Please specify generate repot, email dev, or email qa.')
