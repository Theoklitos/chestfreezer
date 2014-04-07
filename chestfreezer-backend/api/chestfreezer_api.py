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

WEB_INTERFACE_ROOT = "/chestfreezer"
API_ROOT = WEB_INTERFACE_ROOT + "/api"

FRONTEND_JAVASCRIPT_FILENAME = "graphs.html"
FRONTEND_JAVASCRIPT_FILE_PATH = os.getcwd() + "/../../chestfreezer-frontend/"
ACCESS_LOG_FILE = os.getcwd() + '/../accessLog'

web_run_thread = None 

def _log_and_print_security_message(message):
    """ logs and prints the given message to a file, used for logging security access """
    print message    
    if configuration._should_log_security: misc_utils.append_to_file(ACCESS_LOG_FILE, message)  

def do_auth_check():
    """ checks the user's credential with what is in the config """    
    authorized = False
    blocked_ip = False
    ip = 'Unknown IP' 
    pretty_now_datetime = misc_utils.timestamp_to_datetime(time.time()).strftime("%c")   
    enviroment_list = request.environ
    if enviroment_list.get('REMOTE_ADDR') is None:
        ip = enviroment_list.get('REMOTE_ADDR')
        blocked_ip = configuration.is_ip_allowed(ip) | (ip == 'Unknown IP')
    if not configuration.is_security_enabled(): 
        authorized = True
    elif request.auth is not None:        
        user, password = request.auth
        blocked_ip = ip not in configuration.is_ip_allowed()
        if (user == configuration.web_user()) & (password == configuration.web_pwd()) & (not blocked_ip):    
            authorized = True    
    if authorized:
        _log_and_print_security_message(pretty_now_datetime + ': Address [' + ip + '] accessed the API')
        return # all good
    else:
        message = pretty_now_datetime + ': Unauthorized access from [' + ip + ']'         
        _log_and_print_security_message(message)
        if blocked_ip: emailer.escalate("Unauthorized access", message)
        abort(401,"This method requires basic authentication")

def _log_and_escalate(error_code, message):
    """ logs an error message and aborts """
    print 'Error code: ' + str(error_code) + '. Message: ' + message
    emailer.escalate("Chestfreezer Error " + str(error_code), "Error code " + str(error_code) + "\n\nMessage: " + message)                    
    abort(error_code, message)    

def chestfreezer_call_decorator(fn):    
    def wrapper_function(*args, **kwargs):
        do_auth_check()    
        try:
            return fn(*args, **kwargs);
        except HTTPError as e:                  
            _log_and_escalate(e.status, e.output)
            raise e
        except Exception as e:                       
            _log_and_escalate(500, "Unspecified error: " + str(e))
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
    except (TypeError, ValueError) as e:
        abort(400, "Malformed timestamp parameter(s): " + str(e))
    
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

