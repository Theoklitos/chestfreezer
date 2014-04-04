'''
Created on Apr 4, 2014

A simple rest(?) api to be used to access the functionality

@author: theoklitos
'''
import web
import time
from database import mysql_adapter

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
        '/chestfreezer_api/temperatures', 'temperatures',
        '/chestfreezer_api/probes', 'probes',
        '/chestfreezer_api/instructions', 'instructions'                
)
    
def run():
    """ call to web.py run(), starts the web stuff """
    app = web.application(urls, globals())
    app.run()
    
    
    
    
    
