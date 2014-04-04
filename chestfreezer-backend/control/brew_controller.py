'''
Created on Apr 3, 2014

Controls the temperature based on readings and user input. Sort of the main logic class.

@author: theoklitos
'''
from database import mysql_adapter

temperature_overwrite = None
temperature_from_instructions = None


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


def set_temperature(temperature_C):
    """ uses the GPIO to turn devices on/off so as to set the temperature """
    