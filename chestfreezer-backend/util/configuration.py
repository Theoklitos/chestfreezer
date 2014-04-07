'''
Created on Apr 2, 2014

Contains properties that are read from a config file. Provides sensible defaults.

@author: theoklitos
'''

import os
import util.SimpleConfigParser as SimpleConfigParser
from ConfigParser import NoOptionError
import re

CONFIGURATION_FILE_NAME = 'configuration'

DEFAULT_HEATER_PIN = '3'
DEFAULT_FREEZER_PIN = '5'
DEFAULT_DB_HOST = 'localhost'
DEFAULT_DB_USER = 'brewmaster'
DEFAULT_DB_PASSWORD = 'h3f3w3iz3n'
DEFAULT_DB_NAME = 'chestfreezer'
DEFAULT_STORE_TEMPERATURE_INTERVAL_SECONDS = 5
store_interval_overwrite = None
DEFAULT_INSTRUCTION_CHECK_INTERVAL_SECONDS = 60
instruction_interval_overwrite = None
DEFAULT_WEB_USER = 'brewmaster'
DEFAULT_WEB_PASSWORD = 'h3f3w3iz3n'
DATABASE_IN_DISK_CONFIG_VALUE = 'disk'
DATABASE_IN_MEMORY_CONFIG_VALUE = 'memory' 
DEFAULT_DB_TYPE = 'disk'
DEFAULT_PORT = 80

DEFAULT_EMAILS_TO_NOTIFY = ''
DEFAULT_EMAILS_TO_WARN = ''

_should_log_security = True
_should_send_emails = True
_is_security_enabled = True

def does_config_file_exist():
    return config_file is not None

def find_config_file(name):    
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    for root, dirs, files in os.walk(path):  # @UnusedVariable
        if name in files:
            return os.path.join(root, name)

Config = SimpleConfigParser.SimpleConfigParser()
config_file = find_config_file(CONFIGURATION_FILE_NAME);
if does_config_file_exist():
    print 'Using configuration file: ' + config_file + '.'
    try:
        Config.read(config_file)        
    except Exception as config_exception:
        print 'Could not read configuration file, reason: ' + str(config_exception) + '.\nWill use default configuration values.'
else:
    print 'No configuration file found, will use default configuration values.'

def _get_array_option_with_default(option_name, default_value):
    """ returns a list (trimmed) from a comma-separated value """
    pattern = re.compile('\s*,\s*')    
    result =  pattern.split(_get_option_with_default(option_name, default_value))
    if (len(result) == 1) & (not result[0].strip()):
        return []     
    else:
        return result
    
def _get_option_with_default(option_name, default_value):
    """ if the option exists, returns its value. If it is empty or does not exist, returns the default value"""
    try:
        option_value = Config.getoption(option_name)        
        if not option_value:
            raise NoOptionError
        else:
            return option_value
    except NoOptionError:
        return default_value    

def set_store_temperature_interval_seconds(seconds):
    """ sets every how many seconds should the temperature readings be stored in the DB """
    global store_interval_overwrite
    store_interval_overwrite = seconds

def store_temperature_interval_seconds():
    """ returns every how many seconds should the temperature readings be stored in the DB """
    if store_interval_overwrite is None:
        return float(_get_option_with_default('temperature_store_interval_time_seconds', DEFAULT_STORE_TEMPERATURE_INTERVAL_SECONDS))
    else:
        return float(store_interval_overwrite)

def db_type():
    """ returns the database type: disk or memory """
    option = _get_option_with_default('db_type', DEFAULT_DB_TYPE).lower()
    if option not in [DATABASE_IN_DISK_CONFIG_VALUE, DATABASE_IN_MEMORY_CONFIG_VALUE]:
        raise Exception('Database type "' + option + '" was not understood. Type must be set to either "memory" or "disk"(default).')
    else:
        return option

def web_user():
    """ returns the username for authentication in the web interface """
    return _get_option_with_default('web_user', DEFAULT_WEB_USER)

def web_pwd():
    """ returns the password for authentication in the web interface """
    return _get_option_with_default('web_pwd', DEFAULT_WEB_PASSWORD)

def heater_pin():
    """ returns the GPIO pin # that controls the heater, which is the 1st plug in the relay """
    return _get_option_with_default('heater_pin', DEFAULT_HEATER_PIN)    

def freezer_pin():
    """ returns the GPIO pin # that controls the freezer, which is the 2nd plug in the relay """
    return _get_option_with_default('freezer_pin', DEFAULT_FREEZER_PIN)
    
def db_host():
    """ where is the mysql database hosted? """
    return _get_option_with_default('db_host', DEFAULT_DB_HOST)
    
def db_user():
    """ the user name that has access to the database """
    return _get_option_with_default('db_user', DEFAULT_DB_USER)

def db_pwd():    
    """ the password for the db user """
    return _get_option_with_default('db_password', DEFAULT_DB_PASSWORD)

def db_name():
    """ which database should our app use? """
    return _get_option_with_default('db_name', DEFAULT_DB_NAME)

def instruction_interval_seconds():
    """ returns every how many seconds there should be a check for new instructions """
    if instruction_interval_overwrite is None:
        return float(_get_option_with_default('instruction_check_interval_time_seconds', DEFAULT_INSTRUCTION_CHECK_INTERVAL_SECONDS))
    else:
        return float(instruction_interval_overwrite)

def set_instruction_interval_seconds(seconds):
    """ sets every how many seconds should there be a check for new instructions """
    global instruction_interval_overwrite
    instruction_interval_overwrite = seconds

def port():
    """ which port should the web interface run on """
    return int(_get_option_with_default('port', DEFAULT_PORT))

def emails_to_warn():
    """ who should get warning about errors messages in the chestfreezer? """
    return _get_array_option_with_default('emails_to_warn', DEFAULT_EMAILS_TO_WARN) 

def emails_to_notify():
    """ who should get notifications from the chestfreezer? """
    return _get_array_option_with_default('emails_to_notify', DEFAULT_EMAILS_TO_NOTIFY)

def set_should_send_emails(should):
    """ sets if the email should be send or not """
    global _should_send_emails    
    _should_send_emails = should

def should_send_emails():
    """ is the emailer enabled? this can be set only at runtime """
    return _should_send_emails

def set_is_security_enabled(should):
    """ sets whether the web interface (basic auth) security should be enabled or not """
    global _is_security_enabled
    _is_security_enabled = should
    
def is_security_enabled():
    """ should the api check basic auth credentials """
    return _is_security_enabled

def is_ip_allowed(ip):
    """ returns true if the given IP is allowed to access the api """
    allowed_ips =_get_array_option_with_default('allowed_ips', '')    
    return (not allowed_ips) | (len(allowed_ips)== 0) | (ip in allowed_ips)    
         


