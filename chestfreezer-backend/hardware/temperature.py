'''
Created on Apr 2, 2014

Initializes and takes readings from the temperature sensors

@author: theoklitos
'''
import commands
import os

TEMPERATURE_PROBE_PATH = '/sys/bus/w1/devices' 

class TempReading():            
    def __self__(self, temperature_value, timestamp):
        self.temperature = temperature_value
        self.timestamp = timestamp

def getTemperatureReadings():
    # get probe names    
    for root, dirs, files in os.walk(TEMPERATURE_PROBE_PATH): # @UnusedVariable
        print dirs
        
        
