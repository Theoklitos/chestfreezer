'''
Created on Apr 4, 2014

A simple rest(?) api to be used to access the functionality

@author: theoklitos
'''
import bottle
from bottle import static_file, request, response, abort, HTTPError
import os
from util import configuration, json_parser, misc_utils, emailer
from database import db_adapter
import time
from threading import Thread
import sys

WEB_INTERFACE_ROOT = "/chestfreezer"
API_ROOT = WEB_INTERFACE_ROOT + "/api"

FRONTEND_JAVASCRIPT_FILENAME = "graphs.html"
FRONTEND_JAVASCRIPT_FILE_PATH = os.getcwd() + "/../../chestfreezer-frontend/"

web_run_thread = None

def do_auth_check():
    """ checks the user's credential with what is in the config """
    if request.auth is None:
        abort(401,"This method requires basic authentication")
    user, password = request.auth            
    if (user == configuration.web_user()) & (password == configuration.web_pwd()):    
        return True
    else:
        return False

def _log_and_escalate(error_code, message, exception):
    """ logs an error message and returns the given erroneous status code """
    print 'Error code: ' + str(error_code), 'Message: ' + message + ", exception: " + str(exception)
    emailer.escalate("Chestfreezer Error " + str(error_code), message + "\n\nException: " + str(exception))                
    abort(error_code, message)    

def chestfreezer_call_decorator(fn):    
    def wrapper_function(*args, **kwargs):
        #do_auth_check()    
        try:
            return fn(*args, **kwargs);
        except HTTPError as e:                        
            _log_and_escalate(e.exception, "Unspecified error: " + str(e), str(e.exception))
            raise e
        except Exception as e:            
            _log_and_escalate(500, "Unspecified error: " + str(e), sys.exc_info()[0].__name__)
            raise e
    return wrapper_function

@bottle.get(API_ROOT + '/temperature', apply=[chestfreezer_call_decorator])
def get_temperatures():        
    start_timestamp = 1
    end_timestamp = int(time.time())    
    if request.query_string:    
        start_timestamp = request.query.start
        end_timestamp = request.query.end
        if (not start_timestamp) | (not end_timestamp):
            abort(400, "Provide both 'start' and 'end' timestamp query parameters")
    try:
        print 'Asked for temperature readings from ' + misc_utils.timestamp_to_datetime(float(start_timestamp)).strftime("%c") + ' to ' + misc_utils.timestamp_to_datetime(float(end_timestamp)).strftime("%c") + '...',                    
        all_readings = db_adapter.get_temperature_readings(int(start_timestamp), int(end_timestamp))
        print 'got ' + str(len(all_readings)) + ' result(s).'
        response.content_type = 'application/json;'                
        return json_parser.get_temperature_reading_array_as_json(all_readings)    
    except TypeError:
        abort(400, "Malformed timestamp parameter(s)")
    
@bottle.get(WEB_INTERFACE_ROOT)
def js_spa():
    return static_files(FRONTEND_JAVASCRIPT_FILENAME)        

@bottle.get('/<path:path>')
def static_files(path):
    path = path.replace(WEB_INTERFACE_ROOT[1:] + '/', '')    
    if not path:
        abort(404)
    else:       
        return static_file(path, root=FRONTEND_JAVASCRIPT_FILE_PATH)    
    
def start():
    def start_on_different_thread():        
        bottle.run(host='localhost', port=configuration.port())
    global web_run_thread
    web_run_thread = Thread(target=start_on_different_thread, args=())
    web_run_thread.daemon = True
    web_run_thread.start()

