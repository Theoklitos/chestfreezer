'''
Created on Apr 4, 2014

Simple json marshalling utils for the classes in this project

@author: theoklitos
'''
from control import brew_logic


def _pretty_state_identifier(state):
    """ returns 'off' for False and 'on' for True """
    if state:
        return 'on'
    else:
        return 'off'

def get_temperature_reading_array_as_json(temperature_reading_list):
    """ returns a list of temp readings as a json array """
    result = '['
    for temperature_reading in temperature_reading_list:
        result += '\n' + get_temperature_reading_as_json(temperature_reading) + ','
    if len(temperature_reading_list) != 0:
        result = result[:-1] 
    return result + '\n]'
    
def get_temperature_reading_as_json(temperature_reading):
    """ returns a single temp reading as a json object """    
    result = '{\n  "probe_id" : "' + temperature_reading.probe_id + '",\n  "temperature_C" : "' + str(temperature_reading.temperature_C) + '",\n  "temperature_F" : "' + str(temperature_reading.temperature_F) + '",\n  "timestamp" : "' + str(temperature_reading.timestamp) + '"\n}'
    return result

def get_heater_device_json():
    """ returns information about the heater in json """
    return '{\n    "state" : "' + _pretty_state_identifier(brew_logic.heater_state) + '",\n    "overridden" : "' + str(brew_logic.heater_override).lower() + '"\n  }'

def get_freezer_device_json():
    """ returns information about the freezer in json """
    return '{\n    "state" : "' + _pretty_state_identifier(brew_logic.freezer_state) + '",\n    "overridden" : "' + str(brew_logic.freezer_override).lower() + '"\n  }'

def get_both_devices_json():
    """ returns information about both the freezer and the heater as a json object """
    return '{\n  "heater" : ' + get_heater_device_json() + ',\n  "freezer" : ' + get_freezer_device_json() + '\n}'

def get_probe_array_as_json(probe_list):
    """ returns a list of temp probes as a json array """
    result = '['
    for probe in probe_list:
        result += '\n' + get_probe_as_json(probe) + ','
    return result[:-1] + '\n]'

def get_probe_as_json(probe):
    """ returns a single temp probe  as a json object """
    master_value = 'False'
    if probe.master == 1:
        master_value = 'True'
    result = '{\n  "probe_id" : "' + str(probe.probe_id) + '",\n  "name" : "' + str(probe.name) + '",\n  "master" : "' + master_value + '"\n}'
    return result 
    

