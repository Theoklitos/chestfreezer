'''
Created on Apr 4, 2014

A simple rest(?) api to be used to access the functionality

@author: theoklitos
'''
import web
import time
from database import mysql_adapter
import sys
from util import json_parser, configuration
from control import brew_controller
from hardware import temperature

def _is_authenticated():
    """ checks if the user is authenticated, by his sessions """
    #return session.login == 1 TODO
    return True
    
def _auth_check():
    """ checks if user is authenticated and throws exception if he isn't """
    try:
        if not _is_authenticated():
            raise web.unauthorized()
    except:
        raise web.unauthorized()
    
class session:
    """ security controller """
    def POST(self):
        variables = web.input()
        if (variables.get('username') == configuration.web_user()) & (variables.get('password') == configuration.web_pwd()):
            user_session.login = 1
            print 'Logged in.'
            return web.ok()           
        else:
            user_session.login = 0
            return web.unauthorized()          
    def DELETE(self):
        user_session.login = 0        
    
class temperature:
    """ temperature controller """
    def GET(self):       
        _auth_check()
        variables = web.input()        
        if len(variables) == 0:        
            all_readings = mysql_adapter.get_readings(1, int(time.time()))
            return json_parser.get_temperature_reading_array_as_json(all_readings)
        elif len(variables) == 1:
            if ('master' in variables) | ('Master' in variables) | ('MASTER' in variables):                                
                return json_parser.get_temperature_reading_as_json(temperature.last_master_reading)            
        elif len(variables) == 2:
            try:
                from_timestamp = float(variables.get('from'))
                to_timestamp = float(variables.get('to'))
                all_readings = mysql_adapter.get_readings(from_timestamp, to_timestamp)
                return json_parser.get_temperature_reading_array_as_json(all_readings)
            except Exception as e:
                print 'Error calling temperature endpoint: ' + str(e)
                raise web.badrequest()            
        else:
            raise web.badrequest()        
    def POST(self):
        _auth_check()
        pass

class devices:
    """ plural temperature controller """
    def GET(self):
        _auth_check()
        return json_parser.get_both_devices_json()        
                    
class device:
    """ single temperature controller """
    def _is_heater(self, name):
        return name in ['heater', 'Heater', 'HEATER']
        
    def _is_freezer(self, name):
        return name in name in ['freezer', 'Freezer', 'FREEZER']
    
    def GET(self, name):
        _auth_check()
        if self._is_heater(name):
            return json_parser.get_heater_device_json()
        elif self._is_freezer(name):
            return json_parser.get_freezer_device_json()
        else:
            raise web.badrequest()
    def POST(self, name):
        _auth_check()
        variables = web.input()        
        if len(variables) != 1:
            try:
                if name is None:
                    raise web.badrequest()                
                raw_state = float(variables.get('state'))
                boolean_state = None
                remove_override = False
                if raw_state in ['on', 'ON', 'On', 'True', 'true', 'TRUE']:
                    boolean_state = True
                if raw_state in ['off', 'OFF', 'Of', 'False', 'false', 'FALSE']:
                    boolean_state = False
                if raw_state in ['remove', 'REMOVE', 'Remove']:
                    remove_override = True
                else:
                    raise web.badrequest()                
                if self._is_heater(name):
                    if remove_override:
                        brew_controller.remove_heater_override()
                    else:
                        brew_controller.set_heater_override(boolean_state)
                elif self._is_freezer(name):
                    if remove_override:
                        brew_controller.remove_freezer_override()
                    else:
                        brew_controller.set_freezer_override(boolean_state)
                else:
                    raise web.badrequest()
            except Exception as e:
                print 'Error calling device endpoint: ' + str(e)
                raise web.badrequest()
        else:        
            raise web.badrequest()
    
class probes:
    """ temperature probe controller """
    def GET(self, probe_id):
        _auth_check()
        if probe_id is None:
            probe_list = mysql_adapter.get_all_probes()
            return json_parser.get_probe_array_as_json(probe_list)
        else:
            return probe_id
    def POST(self, probe_id):
        _auth_check()
        if probe_id is None:
            raise web.badrequest()
        else:
            pass

class instructions:
    """ temperature instructions controller """
    def GET(self):
        _auth_check()
        pass
    def POST(self):
        _auth_check()
        pass
    def DELETE(self):
        _auth_check()
        pass

urls = (
        '/chestfreezer_api/sessions', 'session',
        '/chestfreezer_api/temperature', 'temperature',
        
        '/chestfreezer_api/devices', 'devices',
        '/chestfreezer_api/device/(.+)', 'device',
        
        '/chestfreezer_api/probes', 'probes',
        '/chestfreezer_api/probe/(.+)', 'probe',
        
        '/chestfreezer_api/instructions', 'instructions'          
)
    
app = web.application(urls, globals())
user_session = web.session.Session(app, web.session.DiskStore('sessions'))
web.config.debug = False
    
def run():
    """ call to web.py run(), starts the web stuff """               
    try:    
        app.run()
    except KeyboardInterrupt:
        print 'Interrupted, shutting down...'
    #    # stop threads, etc?
        import hardware.chestfreezer_gpio as gpio
        gpio.cleanup()
        sys.exit("Goodbye!")
    
    
    
    
    
