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
parser.add_option('-q', '--qa', type='string', dest='QA', help='location of file w/ list of qe')

(opts, args) = parser.parse_args()


bugzilla = Bugzilla36(url='https://bugzilla.redhat.com/xmlrpc.cgi', user=opts.BZUSER, password=opts.BZPASS)



def email_onqa():
    print('PRINT MY ON_QA BUGS')
    for line in fileinput.input(opts.QA):
        onqa_dict = {
                     'product': opts.PRODUCT,
                     'bug_status':'ON_QA',
                     'qa_contact':''
                     }
        print(line)
        onqa_dict['qa_contact'] = line
        print(onqa_dict)
        on_qa_bugs = bugzilla.query(onqa_dict)
        print(on_qa_bugs)
        email_txt = 'Your Current ON_QA bugs \n'
        for thisbug in on_qa_bugs:
            bugnum = str(thisbug)[1:7]
            email_txt += (str(thisbug)+'\n https://bugzilla.redhat.com/show_bug.cgi?id='+bugnum+ '\n\n')
        print email_txt
        msg = MIMEText(email_txt)
        msg['Subject'] = opts.PRODUCT+ " ON_QA Bugs"
        s = smtplib.SMTP('localhost')
        s.sendmail('whayutin@redhat.com', line, msg.as_string())
        s.quit()
       
def email_ondev():
    setOfDevelopers = set([])
    print('PRINT ONDEV BUGS')
    ondevAssignedToDict = {
                        'product': opts.PRODUCT,
                        'bug_status':'ON_DEV,NEW,ASSIGNED,,ON_DEV,MODIFIED,POST'
                           }
    on_dev_bugs = bugzilla.query(ondevAssignedToDict)
    print(on_dev_bugs)
    for thisbug in on_dev_bugs:
        bugnum = str(thisbug)[1:7]
        mybug = bugzilla.getbug(bugnum)
        developer = mybug.__getattribute__('assigned_to')
        setOfDevelopers.add(developer)
        print(developer)
    
    print("THIS IS THE SET UP DEV")
    print(setOfDevelopers)
    for thisDev in setOfDevelopers:
        ondevForThisDevDict = {
                               'product': opts.PRODUCT,
                               'bug_status':'ON_DEV,NEW,ASSIGNED,,ON_DEV,MODIFIED,POST',
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
        s.sendmail('whayutin@redhat.com', thisDev, msg.as_string())
        s.quit()


email_onqa()
#Commented out just for saftely ... dont want to email dev when I'm working on this script
#email_ondev()
