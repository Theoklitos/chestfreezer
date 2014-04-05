'''
Created on Apr 4, 2014

A simple rest(?) api to be used to access the functionality

@author: theoklitos
'''
import web
import time
from database import mysql_adapter
import sys
from util import json_parser
from control import brew_controller


def _pretty_state_identifier(state):
    """ returns 'off' for False and 'on' for True """
    if state:
        return 'on'
    else:
        return 'off'
    
class session:
    """ security controller """
    def POST(self):
        pass
    
class temperatures:
    """ temperature controller """
    def GET(self):        
        variables = web.input()        
        if len(variables) == 0:        
            all_readings = mysql_adapter.get_readings(1, int(time.time()))
            return json_parser.get_temperature_reading_array_as_json(all_readings)
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
        pass
    
class devices:
    """ temperature controller """
    def GET(self):
        heater = '{\n    "state" : "' + _pretty_state_identifier(brew_controller.heater_state) + '",\n    "overridden" : "' + str(brew_controller.heater_override).lower() + '"\n  }'
        freezer = '{\n    "state" : "' + _pretty_state_identifier(brew_controller.freezer_state) + '",\n    "overridden" : "' + str(brew_controller.freezer_override).lower() + '"\n  }'
        return '{\n  "heater" : ' + heater + ',\n  "freezer" : ' + freezer + '\n}'
    def POST(self):
        variables = web.input()        
        if len(variables) != 1:
            try:                
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
                device = float(variables.get('device'))
                if device in ['heater', 'Heater', 'HEATER']:
                    if remove_override:
                        brew_controller.remove_heater_override()
                    else:
                        brew_controller.set_heater_override(boolean_state)
                elif device in ['freezer', 'Freezer', 'FREEZER']:
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
    def GET(self):
        probe_list = mysql_adapter.get_all_probes()
        return json_parser.get_probe_array_as_json(probe_list)
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
        '/chestfreezer_api/devices', 'devices',
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
    
    
    
    
    
