'''
Created on Apr 2, 2014

Contains properties that are read from a config file. Provides sensible defaults.

@author: theoklitos
'''

import os
import util.SimpleConfigParser as SimpleConfigParser
from ConfigParser import NoOptionError

CONFIGURATION_FILE_NAME = 'configuration'

DEFAULT_HEATER_PIN = '3'
DEFAULT_FREEZER_PIN = '5'
DEFAULT_DB_HOST = 'localhost'
DEFAULT_DB_USER = 'brewmaster'
DEFAULT_DB_PASSWORD = 'h3f3w3iz3n'
DEFAULT_DB_NAME = 'chestfreezer'
DEFAULT_STORE_TEMPERATURE_INTERVAL_SECONDS = 5
store_interval_overwrite = None
DEFAULT_WEB_USER = 'brewmaster'
DEFAULT_WEB_PASSWORD = 'h3f3w3iz3n'

def does_config_file_exist():
    return config_file is not None

def find_config_file(name):    
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    for root, dirs, files in os.walk(path): # @UnusedVariable
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
    """ sets every how many seconds should the app store temperature readings in the BD """
    global store_interval_overwrite
    store_interval_overwrite = seconds

def store_temperature_interval_seconds():
    """ returns every how many seconds should the app store temperature readings in the BD """
    if store_interval_overwrite is None:
        return _get_option_with_default('temperature_store_interval_time', DEFAULT_STORE_TEMPERATURE_INTERVAL_SECONDS)
    else:
        return store_interval_overwrite

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


