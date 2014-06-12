'''
Created on Apr 7, 2014

sends notifications, escalations etc to a gmail account

@author: theoklitos
'''
from util import configuration, misc_utils
import smtplib

GMAIL_USERNAME = 'chestfriseur@gmail.com'
GMAIL_PASSWORD = 'h3f3w3iz3n'

def _send_email(subject, body, recipients):
    if not configuration.should_send_emails():        
        return
    """ connects to gmail's smtp server and sends the email """
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(GMAIL_USERNAME, GMAIL_PASSWORD)
    print 'Send email "' + subject + '" to ' + ','.join(recipients) + '.'
    for to in recipients:        
        message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
        """ % (GMAIL_USERNAME, ", ".join(recipients), subject, body)    
        try:
            server.sendmail(GMAIL_USERNAME, to, 'Content-type: text/html\n' + message)                     
        except Exception as e:
            print 'Could not send email: ' + str(e)
    server.quit()

def _get_beer_subject_body(name, from_timestamp, to_timestamp, is_for_tomorrow, verb, noun):
    """ based on the date period and its type, generates an email subject + body """
    pretty_from = misc_utils.get_pretty_date_timestamp(from_timestamp)
    pretty_to = misc_utils.get_pretty_date_timestamp(to_timestamp)
    body = 'The beer named "' + name + '" is scheduled to ' + verb + ' in the period from <strong>' + pretty_from + '</strong> until <strong>' + pretty_to + '</strong>'    
    if is_for_tomorrow:
        subject = name + ' is to begin ' + noun + ' tomorrow'
        body += ', which begins tomorrow. <br><br>You have one day to prepare!'
    else:
        subject = name + ' should begin ' + noun + ' today'
        body += ', which starts today. <br><br>Get to it!'    
    print subject
    return subject,body

def send_fermentation_email(beer, is_for_tomorrow):
    """ when its time to ferment the beer """        
    subject, body = _get_beer_subject_body(beer.name, beer.fermenting_from_timestamp, beer.fermenting_to_timestamp, is_for_tomorrow, 'ferment', 'fermentation')
    notify(subject,body)

def send_dryhopping_email(beer, is_for_tomorrow):
    """ when its time to dry-hop the beer """
    subject, body = _get_beer_subject_body(beer.name, beer.fermenting_from_timestamp, beer.fermenting_to_timestamp, is_for_tomorrow, 'dry-hop', 'dry-hopping')
    notify(subject,body)

def send_conditioning_email(beer, is_for_tomorrow):
    """ when its time to condition the beer """
    subject, body = _get_beer_subject_body(beer.name, beer.fermenting_from_timestamp, beer.fermenting_to_timestamp, is_for_tomorrow, 'condition', 'conditioning')
    notify(subject,body)

def escalate(subject, message):
    """ when something bad happened """
    _send_email(subject, message, configuration.emails_to_warn())

def notify(subject, message):
    """ when something of interest happened """    
    _send_email(subject, message, configuration.emails_to_notify())

if __name__ == "__main__":
    notify("test subject", "test body")
