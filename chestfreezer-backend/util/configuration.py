'''
Created on Apr 2, 2014

Contains properties that are read from a config file. Provides sensible defaults.

@author: theoklitos
'''

import os
import util.SimpleConfigParser as SimpleConfigParser
from ConfigParser import NoOptionError

CONFIGURATION_FILE_NAME = 'configuration'

DEFAULT_DEVICE1_PIN = 3
DEFAULT_DEVICE2_PIN = 5
DEFAULT_DB_HOST = 'localhost'
DEFAULT_DB_USER = 'brewmaster'
DEFAULT_DB_PASSWORD = 'h3f3w3iz3n'
DEFAULT_DB_NAME = 'chestfreezer'

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

def get_option_with_default(option_name, default_value):
    """ if the option exists, returns its value. If it is empty or does not exist, returns the default value"""
    try:
        option_value = Config.getoption(option_name)        
        if not option_value:
            raise NoOptionError
        else:
            return option_value
    except NoOptionError:
        return default_value

def device1_pin():
    """ returns the GPIO pin # that controls the 1st plug in the relay """
    return get_option_with_default('device1_pin', DEFAULT_DEVICE1_PIN)    

def device2_pin():
    """ returns the GPIO pin # that controls the 2nd plug in the relay """
    return get_option_with_default('device2_pin', DEFAULT_DEVICE2_PIN)
    
def get_db_host():
    """ where is the mysql database hosted? """
    return get_option_with_default('db_host', DEFAULT_DB_HOST)
    
def get_db_user():
    """ the user name that has access to the database """
    return get_option_with_default('db_user', DEFAULT_DB_USER)

def get_db_pwd():    
    """ the password for the db user """
    return get_option_with_default('db_password', DEFAULT_DB_PASSWORD)
    
def get_db_name():
    """ which database should our app use? """
    return get_option_with_default('db_name', DEFAULT_DB_NAME)