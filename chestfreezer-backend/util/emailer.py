'''
Created on Apr 7, 2014

sends notifications, escalations etc to a gmail account

@author: theoklitos
'''
from util import configuration
import smtplib

GMAIL_USERNAME = 'chestfriseur@gmail.com'
GMAIL_PASSWORD = 'h3f3w3iz3n'

def _send_email(subject, body, to):
    if not configuration.should_send_emails():        
        return
    """ connects to gmail's smtp server and sends the email """
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(GMAIL_USERNAME, GMAIL_PASSWORD)
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (GMAIL_USERNAME, ", ".join(to), subject, body)    
    try:
        server.sendmail(GMAIL_USERNAME, to, message)        
        server.quit()
        print 'Send email "' + subject + '" to ' + ','.join(to) + '.'         
    except Exception as e:
        print 'Could not send email: ' + str(e)

def escalate(subject, message):
    """ when something bad happened """
    _send_email(subject, message, configuration.emails_to_warn())

def notify(subject, message):
    """ when something of interest happened """    
    _send_email(subject, message, configuration.emails_to_notify())

if __name__ == "__main__":
    notify("test subject", "test body")
