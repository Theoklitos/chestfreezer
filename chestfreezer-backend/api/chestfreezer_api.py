'''
Created on Apr 4, 2014

A simple rest(?) api to be used to access the functionality

@author: theoklitos
'''
import bottle
from bottle import static_file, request, response, abort
import sys
import os
from util import configuration, json_parser, misc_utils
from database import db_adapter
import time

WEB_INTERFACE_ROOT = "/chestfreezer/"
API_ROOT = WEB_INTERFACE_ROOT + "api"

FRONTEND_JAVASCRIPT_FILENAME = "graphs.html"
FRONTEND_JAVASCRIPT_FILE_PATH = os.getcwd() + "/../../chestfreezer-frontend/"

def access_control(user, password):
    """ very simple basic auth """
    if (user == configuration.web_user()) & (password == configuration.web_pwd()):    
        return True
    else:
        return False

def _abort_and_log(error_code, message, exception):
    """ logs an error message and returns the given erroneous status code """
    print message + " - exception: " + str(exception)        
    abort(error_code, message)
        
@bottle.get(API_ROOT + '/temperature')
def get_temperatures():
    start_timestamp = 1
    end_timestamp = int(time.time())    
    if request.query_string:    
        start_timestamp = request.query.start
        end_timestamp = request.query.end
        if (not start_timestamp) | (not end_timestamp):
            abort(400, "Provide both 'start' and 'end' timestamp query parameters")
    try:                        
        print 'Asked for temperature readings from ' + misc_utils.timestamp_to_datetime(float(start_timestamp)).strftime("%c") + ' to ' + misc_utils.timestamp_to_datetime(float(end_timestamp)).strftime("%c")
        all_readings = db_adapter.get_temperature_readings(int(start_timestamp), int(end_timestamp))
        response.content_type = 'application/json;'                
        return json_parser.get_temperature_reading_array_as_json(all_readings)
    except Exception as e:
        _abort_and_log(400, "Malformed timestamp parameter(s)", e)
    
@bottle.get(WEB_INTERFACE_ROOT + "/")
def js_spa():
    return static_files(FRONTEND_JAVASCRIPT_FILENAME)        

@bottle.get('/<path:path>')
def static_files(path): 
    if not path:
        abort(404)
    else:       
        return static_file(path, root=FRONTEND_JAVASCRIPT_FILE_PATH)    
    
def run_on_different_thread():
    """ TODO """
    try:    
        bottle.run(host='localhost', port=configuration.port())    
    except KeyboardInterrupt:
        print 'Interrupted, shutting down...'
        # stop threads, etc?
        import hardware.chestfreezer_gpio as gpio
        gpio.cleanup()
        sys.exit("Goodbye!")
    except Exception as e:
        print 'exception: ' + str(e)
    
