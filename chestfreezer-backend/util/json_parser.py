'''
Created on Apr 4, 2014

Simple json marshalling utils for the classes in this project

#TODO Note: This whole module is pointless! Bottle.py can easily marshal dictionaries into/from json!

@author: theoklitos
'''
from control import brew_logic
from util import misc_utils, configuration
from database import db_adapter

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
    
def get_instruction_as_json(instruction):
    """ returns a single instruction as a json object """
    result = '{\n  "instruction_id" : "' + instruction.instruction_id + '",\n  "target_temperature_C" : "' + str(instruction.target_temperature_C) + '",\n  "from_timestamp" : "' + str(instruction.from_timestamp) + '",\n  "to_timestamp" : "' + str(instruction.to_timestamp) + '",\n  "description" : "' + instruction.description + '"\n}'
    return result

def get_instruction_array_as_json(instruction_list):
    """ returns the given instruction array as a json list """
    result = '['
    for instruction in instruction_list:
        result += '\n' + get_instruction_as_json(instruction) + ','
    if len(instruction_list) != 0:
        result = result[:-1] 
    return result + '\n]'    

def get_target_temperature_json():
    """ returns information about the current "target" temperature """
    is_overriden = False    
    if brew_logic.temperature_override_C is not None:
        actual_target_C = brew_logic.temperature_override_C
        is_overriden = True
    elif brew_logic.instruction_target_temperature_C is not None: actual_target_C = brew_logic.instruction_target_temperature_C
    elif (brew_logic.instruction_target_temperature_C is None) & (not is_overriden): return 
    if actual_target_C is None: return
    current_instruction_json = ""
    actual_target_F = misc_utils.celsius_to_fahrenheit(actual_target_C)
    if brew_logic.current_instruction_id is not None: current_instruction_json = ',\n"current_instruction_id" : "' + brew_logic.current_instruction_id + '" '
    return '{\n  "target_temperature_C" : ' + str(actual_target_C) + ',\n  "target_temperature_F" : ' + str(actual_target_F) + ',\n  "overridden" : "' + str(is_overriden).lower() + '"' + current_instruction_json + '\n}' 

def get_settings_as_json():
    """ returns the application options as a json object """
    store_temperature_interval_seconds = configuration.store_temperature_interval_seconds()     
    l1 = '  "store_temperature_interval_seconds" : ' + str(int(store_temperature_interval_seconds)) + ',';
    instruction_interval_seconds = configuration.instruction_interval_seconds()
    l2 = '  "instruction_interval_seconds" : ' + str(int(instruction_interval_seconds)) + ',';
    control_temperature_interval_seconds = configuration.control_temperature_interval_seconds()
    l3 = '  "monitor_temperature_interval_seconds" : ' + str(int(control_temperature_interval_seconds)) + ',';
    temperature_tolerance = configuration.temperature_tolerance()
    l4 = '  "temperature_tolerance_C" : ' + str(temperature_tolerance) + ',';        
    database_size = db_adapter.get_database_size()
    l5 = '  "database_size_MB" : ' + str(round(database_size,1)) + ',';
    database_free_size = db_adapter.get_database_free_size()
    l6 = '  "database_free_size_MB" : ' + str(round(database_free_size,1)) + '';
    return '{\n  ' + l1 + '\n  ' + l2 + '\n  ' + l3 + '\n  ' + l4 + '\n  ' + l5 + '\n  ' + l6 + '\n}'
    
def get_beer_as_json(beer):
    """ returns the given beer as a json object """
    return {'beer_id' : beer.beer_id, 'name' : beer.name, 'style' : beer.style, 'fermenting_from' : beer.fermenting_from_timestamp, 'fermenting_to' : beer.fermenting_to_timestamp, 'dryhopping_from' : beer.dryhopping_from_timestamp, 'dryhopping_to' : beer.dryhopping_to_timestamp, 'conditioning_from' : beer.conditioning_from_timestamp, 'conditioning_to' : beer.conditioning_to_timestamp, 'rating' : beer.rating, 'comments' : beer.comments}
    
def get_all_beers_as_json():
    """ returns all the beers in the database as a json array """
    from json import dumps    
    result = []
    for beer in db_adapter.get_all_beers():        
        result.append(get_beer_as_json(beer))        
    return dumps(result)

