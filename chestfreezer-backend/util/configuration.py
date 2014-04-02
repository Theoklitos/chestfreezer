'''
Created on Apr 2, 2014

Contains properties that are read from a config file. Provides sensible defaults.

@author: theoklitos
'''

import os
import util.SimpleConfigParser as SimpleConfigParser

CONFIGURATION_FILE_NAME = 'configuration'

DEFAULT_DEVICE1_PIN = 3
DEFAULT_DEVICE2_PIN = 5

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

# returns the GPIO pin # that controls the 1st plug in the relay
def device1_pin():
    if does_config_file_exist():
        return Config.getoption('device1_pin')
    else:
        return DEFAULT_DEVICE1_PIN

# returns the GPIO pin # that controls the 2nd plug in the relay
def device2_pin():
    if does_config_file_exist():
        return Config.getoption('device2_pin')
    else:
        return DEFAULT_DEVICE2_PIN

