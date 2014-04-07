'''
Created on Apr 6, 2014

Injects test data in the database

@author: theoklitos
'''
from database import db_adapter
from random import randrange
import hardware

PROBE1_ID = "123456"  # high value
PROBE2_ID = "3337EA"  # average
PROBE3_ID = "999909"  # low

def insert_test_temperatures(number_of_readings_per_probe=1000):
    """ injects the given number of temperature readings in the given database """    
    readings = []
    probe_ids = hardware.temperature_probes.probe_ids        
    for _x in range(1, number_of_readings_per_probe):        
        for probe_id in probe_ids:            
            readings.append(get_temperature_for_probe(probe_id))
    db_adapter.store_temperatures(readings)            
    db_adapter.db.commit()
    print 'Added ' + str(number_of_readings_per_probe * len(probe_ids)) + ' test temperature readings.'

def get_temperature_for_probe(probe_id):
    """ returns a fake temperature for the given probe_id """
    temperature_C = None
    if probe_id == PROBE1_ID:
        temperature_C = 21 + randrange(20)
    elif probe_id == PROBE2_ID:
        temperature_C = 11 + randrange(15)
    elif probe_id == PROBE3_ID:
        temperature_C = -4 + randrange(10)        
    else:
        temperature_C = -9 + randrange(30)  # whatever value
    return hardware.temperature_probes.TemperatureReading(probe_id, temperature_C)


