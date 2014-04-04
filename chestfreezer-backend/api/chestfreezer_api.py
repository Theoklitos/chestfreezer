'''
Created on Apr 4, 2014

A simple rest(?) api to be used to access the functionality

@author: theoklitos
'''
import web
import time
from database import mysql_adapter
import sys

class session:
    """ security controller """
    def POST(self):
        pass
    
class temperatures:
    """ temperature controller """
    def GET(self):        
        all_readings = mysql_adapter.get_readings(1, int(time.time()))
        return all_readings
    def POST(self):
        pass

class probes:
    """ temperature probe controller """
    def GET(self):        
        pass
    def POST(self):
        pass

class instructions:
    """ temperature instructions controller """
    def GET(self):
        pass
    def POST(self):
        pass
    def DELETE(self):
        pass

urls = (
        '/chestfreezer_api/session', 'session',
        '/chestfreezer_api/temperatures', 'temperatures',
        '/chestfreezer_api/probes', 'probes',
        '/chestfreezer_api/instructions', 'instructions'                
)
    
def run():
    """ call to web.py run(), starts the web stuff """
    app = web.application(urls, globals())
    try:
        app.run()
    except KeyboardInterrupt:
        print 'Interrupted, shutting down...'
        # stop threads, etc?
        import hardware.chestfreezer_gpio as gpio
        gpio.cleanup()
        sys.exit("Goodbye!")
    
    
    
    
    
