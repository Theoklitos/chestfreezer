'''
Created on Apr 3, 2014

Controls the temperature based on readings and user input. Sort of the main logic class.

@author: theoklitos
'''
from database import mysql_adapter
#from hardware import chestfreezer_gpio
from util import configuration

temperature_override = None
temperature_from_instructions = None

freezer_override = False
freezer_state = False
heater_override = False
heater_state = False

class Instruction():
    """ an instruction that dictates what the temperature(C) should be, and in which time period it should be so """
    def __init__(self, start_timestamp, end_timestamp, description='No description given'):
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.description = description

def set_temperature_overwrite(temperature_C):
    """ will set the temperature to the given degree (C), overwriting any other instructions """
    global temperature_overwrite
    temperature_overwrite = float(temperature_C)

def get_current_instruction():
    """ looks in the database and determines what the controller should be doing now """
    if temperature_overwrite is not None:
        set_temperature(temperature_overwrite)
    else :
        result = mysql_adapter.get_instructions_for_time()
        if len(result) > 1:
            raise
        pass

def _set_heater(should_activate):
    """ sets the heater state to on/off directly """
    global heater_state
    heater_state = not should_activate
    #chestfreezer_gpio.output_pin(configuration.heater_pin(), not should_activate) 

def _set_freezer(should_activate):
    """ sets the freezer state to on/off directly """
    global freezer_state
    freezer_state = not should_activate
    #chestfreezer_gpio.output_pin(configuration.freezer_pin(), not should_activate) 
        
def remove_heater_override():
    """ removes any override to the heater state """
    global heater_override 
    heater_override = False
    #TODO instruction call asap
    #TODO
    #TODO
    #TODO

def remove_freezer_override():
    """ removes any override to the freezer state """
    global freezer_override 
    freezer_override = False
    #TODO instruction call asap
    #TODO
    #TODO
    #TODO    
    
def set_heater_override(should_activate):
    """ turns the heater on or off regardless of instructions """
    global heater_override 
    heater_override = True
    _set_heater(should_activate)    
    
def set_freezer_override(should_activate):
    """ turns the freezer on or off regardless of instructions """
    global freezer_override
    freezer_override = True
    _set_freezer(should_activate)

def set_temperature(temperature_C):
    """ uses the GPIO to turn devices on/off so as to set the temperature """
    