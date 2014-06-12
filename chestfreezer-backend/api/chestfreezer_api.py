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
from control import brew_logic
from hardware import temperature_probes
import traceback
from control.brew_logic import InstructionException, Instruction, BeerException

WEB_INTERFACE_ROOT = "/chestfreezer"
API_ROOT = WEB_INTERFACE_ROOT + "/api"

FRONTEND_INDEX_FILENAME = "index.html"
FRONTEND_JAVASCRIPT_FILE_PATH = os.getcwd() + "/../../chestfreezer-frontend/"
ACCESS_LOG_FILE = os.getcwd() + '/../accessLog'

web_run_thread = None 

def _is_heater(name):
    """ returns true if the given name matches the heater name """
    return name.strip().lower() == 'heater'
        
def _is_freezer(name):
    """ returns true if the given name matches the freezer name """    
    return name.strip().lower() == 'freezer'
    
def _log_and_print_security_message(message):
    """ logs and prints the given message to a file, used for logging security access """
    print message    
    if configuration._should_log_security: misc_utils.append_to_file(ACCESS_LOG_FILE, message)  

def enable_cors(fn):
    """ used to enable cross-site requests """
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if bottle.request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*args, **kwargs)

    return _enable_cors

def _do_auth_check():
    """ checks the user's credential with what is in the config """        
    authorized = False
    allowed_ip = False
    ip = 'Unknown IP' 
    pretty_now_datetime = misc_utils.timestamp_to_datetime(time.time()).strftime("%c")   
    enviroment_list = request.environ
    
    if enviroment_list.get('REMOTE_ADDR') is not None:
        ip = enviroment_list.get('REMOTE_ADDR')
    if enviroment_list.get('REMOTE_ADDR') is None:        
        allowed_ip = configuration.is_ip_allowed(ip) | (ip == 'Unknown IP')    
    if not configuration.is_security_enabled(): 
        authorized = True
    elif request.auth is not None:        
        user, password = request.auth
        allowed_ip = configuration.is_ip_allowed(ip)        
        # print user + '==' + configuration.web_user() + ':' + str(user == configuration.web_user())
        # print password + '==' + configuration.web_pwd() + ':' + str(password == configuration.web_pwd())
        if (user == configuration.web_user()) & (password == configuration.web_pwd()) & (allowed_ip):    
            authorized = True    
    if authorized:
        # disabled due to spam! need  to find a smarter way for this
        #_log_and_print_security_message(pretty_now_datetime + ': Address [' + ip + '] accessed the API')
        return  # all good
    else:
        message = pretty_now_datetime + ': Unauthorized access from [' + ip + ']'         
        _log_and_print_security_message(message)
        if (not authorized) | (not allowed_ip): emailer.escalate("Unauthorized access", message)
        abort(401, "This method requires basic authentication")

def _log_and_escalate(error_code, message):
    """ logs an error message and aborts """
    tb = traceback.format_exc()
    print 'Error code: ' + str(error_code) + '. Message: ' + message + '\n\n' + tb
    if error_code == 500:
        emailer.escalate("Chestfreezer Error " + str(error_code), "Error code " + str(error_code) + "\n\nMessage: " + message)                    
    abort(error_code, message)    

def _does_parameter_have_value(parameter_name, possible_parameter_values_list, should_abort_if_missing=False, should_abort_if_false=False):
    """ returns true if the given parameter name contains at least one of the possible values """    
    parameter_value = _get_parameter_value(parameter_name, should_abort_if_missing)
    if parameter_value in possible_parameter_values_list:
        return True
    else:
        if should_abort_if_false:
            abort(400, 'Parameter "' + parameter_name + '" should have a value from the following: ' + str(possible_parameter_values_list))
        else:
            return False

def _get_parameter_value(parameter_name, should_abort_if_missing=False):
    """ returns the (first) parameter value for the given parameter name """
    if request.get_header('content-type') == 'application/json':
        json_map = request.json
        parameter_value = json_map.get(parameter_name.strip())
    else:  # otherwise try as a form
        parameter_value = request.forms.get(parameter_name.strip(), None)
    
    if (parameter_value is None) & (should_abort_if_missing):
            abort(400, 'Missing parameter "' + parameter_name + '"')
    return parameter_value

def _get_boolean_value(parameter_name, should_abort_call_if_neither=True):
    """ returns true or false, and aborts the call if the value is neither """
    result = None 
    if _does_parameter_have_value(parameter_name, ['True', 'true', 'TRUE']):
        result = True
    elif _does_parameter_have_value(parameter_name, ['False', 'false', 'FALSE']):
        result = False    
    if (result == None) & (_get_parameter_value(parameter_name) is not None) & should_abort_call_if_neither:
        abort('Parameter "' + parameter_name + '" must be either "true" or "false"')
    return result

def _get_float_value(parameter_name):
    """ parses the parameter to an float, fails if its not one """
    result = _get_parameter_value(parameter_name)     
    if not result:
        return
    try:
        return float(result)
    except:
        abort(400, 'Parameter "' + parameter_name + '" was not an float') 
        
def _get_integer_value(parameter_name):
    """ parses the parameter to an integer, fails if NaN """
    result = _get_parameter_value(parameter_name)     
    if not result:
        return
    try:
        return int(result)
    except:
        abort(400, 'Parameter "' + parameter_name + '" was not an integer')    

def _get_timestamp_parameter(parameter_name, should_abort_if_missing=False):
    """ tries to get a (unix) timestamp parameter as an integer """
    try:
        value = _get_parameter_value(parameter_name, should_abort_if_missing)
        if value is not None:
            return int(value)
    except ValueError:
        abort(400, 'Parameter\'s "' + parameter_name + '" value "' + value + '" is not a valid timestamp.')
    
def _get_timestamp_query_parameters():
    """ returns both a start and an end timestamp parameter, from the query string """
    start_timestamp = 1
    end_timestamp = int(time.time())    
    if request.query_string:    
        start_timestamp = request.query.start  # @UndefinedVariable
        end_timestamp = request.query.end  # @UndefinedVariable
        if (not start_timestamp) | (not end_timestamp):
            abort(400, "Provide both 'start' and 'end' timestamp query parameters")
    return (str(int(start_timestamp)), str(int(end_timestamp)))

def chestfreezer_call_decorator(fn):
    """ the decorator that handles exceptions and security, applied to all calls """    
    def wrapper_function(*args, **kwargs):
        _do_auth_check()
        try:
            return fn(*args, **kwargs);
        except HTTPError as e:                        
            _log_and_escalate(e.status, e.output)
            raise e
        except Exception as e:                       
            _log_and_escalate(500, "Unspecified error: " + str(e))
            raise e
    return wrapper_function



########################## TEMPERATURES #################################################################################
@bottle.get(API_ROOT + '/temperature', apply=[chestfreezer_call_decorator, enable_cors])
def get_temperatures():              
    start_timestamp, end_timestamp = _get_timestamp_query_parameters()
    try:        
        print 'Asked for temperature readings from ' + misc_utils.timestamp_to_datetime(float(start_timestamp)).strftime("%c") + ' to ' + misc_utils.timestamp_to_datetime(float(end_timestamp)).strftime("%c") + '...',
        all_readings = db_adapter.get_temperature_readings(int(start_timestamp), int(end_timestamp))
        print 'got ' + str(len(all_readings)) + ' result(s).'
        response.content_type = 'application/json;'                
        return json_parser.get_temperature_reading_array_as_json(all_readings)    
    except (TypeError, ValueError) as e:
        abort(400, "Malformed timestamp parameter(s): " + str(e))

@bottle.delete(API_ROOT + '/temperature', apply=[chestfreezer_call_decorator, enable_cors])
def delete_temperatures():           
    db_adapter.delete_all_temperatures();
    print 'Deleted all temperature readings.'       
    response.status = 204
        
def _check_for_temperature_override_removal():
    """ checks if there is an override parameter and if its set to False """
    override = _get_boolean_value('override',False)
    if override is not None:
        if not override:
            brew_logic.remove_temperature_override()
            print 'Removed temperature override.'
            response.status = 204
            return True
        elif override:
            abort(400, '"override" value cannot be set to "true" directly')        

@bottle.post(API_ROOT + '/temperature/target', apply=[chestfreezer_call_decorator, enable_cors])
def set_temperature_directly():   
    if _check_for_temperature_override_removal(): return  
    target_temperature_C = _get_parameter_value("target_temperature_C")    
    target_temperature_F = _get_parameter_value("target_temperature_F")
    if (target_temperature_C is not None) & (target_temperature_F is not None):
        abort(400, 'Either set the temperature in Celsius or Fahrenheit, but not both.')    
    if target_temperature_F is not None: target_temperature_C = misc_utils.fahrenheit_to_celsius(float(target_temperature_F))
    brew_logic.set_temperature_overwrite(float(target_temperature_C))
    print 'Target temperature override set to ' + str(target_temperature_C) + 'C/' + str(misc_utils.celsius_to_fahrenheit(float(target_temperature_C))) + 'F'
    response.status = 204

@bottle.get(API_ROOT + '/temperature/target', apply=[chestfreezer_call_decorator, enable_cors])
def get_target_temperature():
    responseJson = json_parser.get_target_temperature_json()
    if not responseJson:
        response.status = 204
    else:  
        return responseJson
##########################################################################################################################



########################## INSTRUCTIONS #################################################################################
def _get_instruction(instruction_id):
    """ tries to get instruction via ID and aborts (404) if it can't be found """
    result = db_adapter.get_instruction_by_id(instruction_id)    
    if result is None:
        abort(404, 'Instruction with ID ' + instruction_id + ' does not exist.')
    return result

@bottle.get(API_ROOT + '/instruction', apply=[chestfreezer_call_decorator, enable_cors])
def get_instructions():    
    if not request.query_string:        
        print 'Returning all instructions...'
        allInstructions = db_adapter.get_instructions(0,2147483648); #end of unix time
        response.content_type = 'application/json;'
        return json_parser.get_instruction_array_as_json(allInstructions)
    if (request.query_string is not None) & ('now' in request.query_string):
        print 'Returning instruction for current time...'
        try:
            return json_parser.get_instruction_as_json(db_adapter.get_instructions()[0])
        except IndexError:
            # no current instruction
            response.status = 204
            return ''
    start_timestamp, end_timestamp = _get_timestamp_query_parameters()
    try:
        print 'Asked for instructions from ' + misc_utils.timestamp_to_datetime(float(start_timestamp)).strftime("%c") + ' to ' + misc_utils.timestamp_to_datetime(float(end_timestamp)).strftime("%c") + '...',
        all_instructions = db_adapter.get_instructions(int(start_timestamp), int(end_timestamp))
        print 'got ' + str(len(all_instructions)) + ' result(s).'
        response.content_type = 'application/json;'                        
        return json_parser.get_instruction_array_as_json(all_instructions)    
    except (TypeError, ValueError) as e:
        abort(400, "Malformed timestamp parameter(s): " + str(e))
    
@bottle.get(API_ROOT + '/instruction/<instruction_id>', apply=[chestfreezer_call_decorator, enable_cors])
def get_instruction(instruction_id):
    instruction = _get_instruction(instruction_id)
    return json_parser.get_instruction_as_json(instruction)

@bottle.delete(API_ROOT + '/instruction/<instruction_id>', apply=[chestfreezer_call_decorator, enable_cors])
def delete_instruction(instruction_id):
    _get_instruction(instruction_id)  # just check if it exists
    db_adapter.delete_instruction(instruction_id)
    print 'Deleted instruction #' + instruction_id
    response.status = 204

@bottle.post(API_ROOT + '/instruction', apply=[chestfreezer_call_decorator, enable_cors])
def create_instruction():
    if _get_parameter_value('instruction_id') is not None:
        abort(400, 'Instruction ID cannot be set directly.')
    target_temperature_C = float(_get_parameter_value("target_temperature_C", True))
    from_timestamp = _get_timestamp_parameter('from_timestamp', True)
    to_timestamp = _get_timestamp_parameter('to_timestamp', True)
    description = _get_parameter_value('description')
    try:
        new_instruction = Instruction(None, target_temperature_C, from_timestamp, to_timestamp, description)
        before_ids = db_adapter.get_all_instruction_ids()
        brew_logic.store_instruction_for_unique_time(new_instruction)
        after_ids = db_adapter.get_all_instruction_ids()    
        new_id = list(set(after_ids) - set(before_ids))[0]
        response.status = 201
        return '{ "instruction_id" : "' + new_id + '" }'  # not really RESTful, maybe will fix at some point
    except InstructionException as e:        
        response.status = 400
        return str(e) # this is the correct way to return errors it seems

@bottle.put(API_ROOT + '/instruction/<instruction_id>', apply=[chestfreezer_call_decorator, enable_cors])
def modify_instruction(instruction_id):
    print 'Updating instruction #' + instruction_id + '...'
    original_instruction = _get_instruction(instruction_id)
    if _get_parameter_value('instruction_id') is not None:
        abort(400, 'Instruction ID cannot be modified')    
    try:
        if _get_parameter_value('target_temperature_C') is not None:
                original_instruction.target_temperature_C = float(_get_parameter_value('target_temperature_C'))            
        original_instruction.set_from_timestamp_safe(_get_timestamp_parameter('from_timestamp'))        
        original_instruction.set_to_timestamp_safe(_get_timestamp_parameter('to_timestamp'))        
        if _get_parameter_value('description') is not None:
            original_instruction.description = str(_get_parameter_value('description')).strip()        
    except (ValueError, TypeError):
        abort(400, 'One or more of the parameter values where malformed')
    try:        
        print str(original_instruction)
        brew_logic.store_instruction_for_unique_time(original_instruction)        
        print 'Modified instruction #' + instruction_id
        response.status = 204
    except InstructionException as e:
        response.status = 400
        return str(e)         
##########################################################################################################################
       
        

########################## PROBES #################################################################################
@bottle.get(API_ROOT + '/probe', apply=[chestfreezer_call_decorator, enable_cors])
def get_all_probes():
    response.content_type = 'application/json;' 
    return json_parser.get_probe_array_as_json(db_adapter.get_all_probes())

@bottle.get(API_ROOT + '/probe/<probe_id>', apply=[chestfreezer_call_decorator, enable_cors])
def get_probe(probe_id):
    probe = db_adapter.get_probe_by_id(probe_id)
    if probe is None:
        abort(400, 'Probe with id "' + probe_id + '" does not exist.')
    else:
        response.content_type = 'application/json;' 
        return json_parser.get_probe_as_json(probe)

@bottle.put(API_ROOT + '/probe/<probe_id>', apply=[chestfreezer_call_decorator, enable_cors])
def set_probe(probe_id):
    probe = db_adapter.get_probe_by_id(probe_id)
    if probe is None:
        abort(400, 'Probe with id "' + probe_id + '" does not exist.')
    else:
        new_name = _get_parameter_value('name')
        master = _get_boolean_value("master")
        if new_name is not None:
            temperature_probes.set_probe_name(probe_id, new_name)
            print 'Set name of probe ' + probe_id + ' to ' + new_name        
        if master is not None:
            if master: 
                temperature_probes.set_probe_as_master(probe_id)
                print 'Probe ' + probe_id + ' is now the master probe.'
            else: 
                temperature_probes.set_probe_as_not_master(probe_id)
                print 'Probe ' + probe_id + ' is no longer the master probe.'                
    response.status = 204
####################################################################################################################



########################## DEVICES #################################################################################
@bottle.get(API_ROOT + '/device', apply=[chestfreezer_call_decorator, enable_cors])
def get_all_devices_state():
    response.content_type = 'application/json;' 
    return json_parser.get_both_devices_json()
    
@bottle.get(API_ROOT + '/device/<device_name>', apply=[chestfreezer_call_decorator, enable_cors])
def get_device_state(device_name):
    response.content_type = 'application/json;' 
    if _is_freezer(device_name):
        return json_parser.get_freezer_device_json()
    elif _is_heater(device_name):
        return json_parser.get_heater_device_json()
    else: 
        abort(400, 'Device "' + device_name + '" is unrecognized. Please use "heater" or "freezer"')    

@bottle.post(API_ROOT + '/device/<device_name>', apply=[chestfreezer_call_decorator, enable_cors])
def set_device_state(device_name):    
    state = None
    if _does_parameter_have_value('state', ['on', 'ON', 'On', 'True', 'true', 'TRUE']):
        state = True
    elif _does_parameter_have_value('state', ['off', 'OFF', 'Off', 'False', 'false', 'FALSE']):
        state = False  
    elif _get_parameter_value('state',False): 
        abort(400, 'Parameter "state" must be either "on"/"true" or "off"/"false"')
        
    override = _get_boolean_value('override')
    if(override is not None) & (not _does_parameter_have_value('override', ['False', 'FALSE', 'False'])):
        abort(400, 'Parameter "override" can only be set to "false"')
    
    if (state is not None) & (override is not None):
        abort(400, 'Either set the "override" value or the "state", but not both.')
    
    if _is_freezer(device_name):
        if state is None:
            brew_logic.remove_freezer_override()
            print 'Removing freezer override...'
        else:
            brew_logic.set_freezer_override(state)
            print 'Overriding freezer to ' + str(state) + '...'
    elif _is_heater(device_name):
        if state is None:
            brew_logic.remove_heater_override()
            print 'Removing heater override...'
        else:
            brew_logic.set_heater_override(state)
            print 'Overriding heater to ' + str(state) + '...'
    else: 
        abort(400, 'Device "' + device_name + '" is unrecognized. Please use "heater" or "freezer"')
    response.status = 204;
####################################################################################################################


########################## SETTINGS #################################################################################
@bottle.get(API_ROOT + '/settings', apply=[chestfreezer_call_decorator, enable_cors])
def get_all_settings():     
    return json_parser.get_settings_as_json()

@bottle.post(API_ROOT + '/settings', apply=[chestfreezer_call_decorator, enable_cors])
def change_settings():    
    store_temperature_interval_seconds = _get_integer_value("store_temperature_interval_seconds")
    if store_temperature_interval_seconds:
        configuration.set_store_temperature_interval_seconds(store_temperature_interval_seconds)
        print 'Set temperature store interval to ' + str(store_temperature_interval_seconds) + ' second(s)'
    instruction_interval_seconds = _get_integer_value("instruction_interval_seconds")
    if instruction_interval_seconds:
        configuration.set_instruction_interval_seconds(instruction_interval_seconds)
        print 'Set instruction check interval to ' + str(instruction_interval_seconds) + ' second(s)'    
    control_temperature_interval_seconds = _get_integer_value("monitor_temperature_interval_seconds")
    if control_temperature_interval_seconds:        
        configuration.set_control_temperature_interval_seconds(control_temperature_interval_seconds)
        print 'Set temperature monitor interval to ' +  str(control_temperature_interval_seconds) + ' second(s)'
    temperature_tolerance = _get_float_value("temperature_tolerance_C")
    if temperature_tolerance:        
        configuration.set_temperature_tolerance_C(temperature_tolerance)
        print 'Set temperature tolerance to ' +  str(temperature_tolerance) + ' C'    
    response.status = 204
####################################################################################################################



########################## BEERS #################################################################################
@bottle.get(API_ROOT + '/beer', apply=[chestfreezer_call_decorator, enable_cors])
def get_all_beers():
    response.status = 200     
    response.content_type = 'application/json'
    return json_parser.get_all_beers_as_json()

@bottle.delete(API_ROOT + '/beer/<beer_id>', apply=[chestfreezer_call_decorator, enable_cors])
def delete_beer(beer_id):
    try:
        beer = db_adapter.get_beer_by_id(beer_id)
        db_adapter.delete_beer_by_name(beer.name)
        response.status = 204
    except BeerException:
        abort(404, 'Beer with id "' + beer_id + '" does not exist')
        
@bottle.put(API_ROOT + '/beer/<beer_id>', apply=[chestfreezer_call_decorator, enable_cors])
def modify_beer(beer_id):
    try:
        beer = db_adapter.get_beer_by_id(beer_id)
    except BeerException:
        abort(404, 'Beer with id ' + beer_id + '" does not exist')   
    # name
    new_name = _get_parameter_value('name')
    if new_name: beer.name = new_name        
    # style
    new_style = _get_parameter_value('style')
    if new_style: beer.style = new_style
    # fermentation
    new_fermenting_from = _get_integer_value('fermenting_from')
    if new_fermenting_from: beer.fermenting_from_timestamp = new_fermenting_from
    new_fermenting_to = _get_integer_value('fermenting_to')
    if new_fermenting_to: beer.fermenting_to_timestamp = new_fermenting_to
    # dryhopping
    new_dryhopping_from = _get_integer_value('dryhopping_from')
    if new_dryhopping_from: beer.dryhopping_from_timestamp = new_dryhopping_from
    new_dryhopping_to = _get_integer_value('dryhopping_to')
    if new_dryhopping_to: beer.dryhopping_to_timestamp = new_dryhopping_to
    # conditioning
    new_conditioning_from = _get_integer_value('conditioning_from')
    if new_conditioning_from: beer.conditioning_from_timestamp = new_conditioning_from
    new_conditioning_to = _get_integer_value('conditioning_to')
    if new_conditioning_to: beer.conditioning_to_timestamp = new_conditioning_to    
    # rating
    new_rating = _get_integer_value('rating')
    if new_rating: beer.rating = new_rating
    # comments
    new_comments = _get_parameter_value('comments')
    if new_comments: beer.comments = new_comments
    # verify & store! 
    try:
        beer._verifyDataMakeSense();
        db_adapter.store_beer(beer)
        response.status = 204
    except BeerException as e:
        abort(400, str(e))
    
@bottle.post(API_ROOT + '/beer', apply=[chestfreezer_call_decorator, enable_cors])
def create_beer():
    beer_name = _get_parameter_value('name',True)
    try:
        db_adapter.get_beer_by_name(beer_name)
        abort(400, 'Beer named "' + beer_name + '" already exists')
    except BeerException:
        new_beer = brew_logic.Beer(beer_name, "Undefined", -1, -1, -1, -1, 0)
        db_adapter.store_beer(new_beer);
        response.status = 204
####################################################################################################################



@bottle.get(WEB_INTERFACE_ROOT)
def index():
    return static_files(FRONTEND_INDEX_FILENAME)        

@bottle.get(WEB_INTERFACE_ROOT + '/')
def index_backslash():
    return index()

@bottle.get('/')
def index_redirect():
    return index()

@bottle.get('/<path:path>')
def static_files(path):
    path = path.replace(WEB_INTERFACE_ROOT[1:] + '/', '')    
    if not path:
        abort(404)
    else:       
        return static_file(path, root=FRONTEND_JAVASCRIPT_FILE_PATH)    
    
def start(server_type="paste"):
    def start_on_different_thread():        
        bottle.run(host='0.0.0.0', port=configuration.port(), server=server_type)
    global web_run_thread
    web_run_thread = Thread(target=start_on_different_thread, args=())
    web_run_thread.daemon = True
    web_run_thread.start()    

