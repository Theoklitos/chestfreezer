'''
Created on Apr 2, 2014

Initializes and takes readings from the temperature probes, also manages the naming/identifying of the sensors themselves

@author: theoklitos
'''

import glob
import subprocess
import time
import database.db_adapter
from util import misc_utils, configuration
from hardware import chestfreezer_gpio
from tests import test_data
from threading import Thread

TEMPERATURE_PROBE_PATH = '/sys/bus/w1/devices/' 
probe_ids = []

last_master_reading = None
master_probe_id = None 

class Probe():
    """ represents a temperature probe """
    def __init__(self, probe_id, name=None, master=False):
        self.probe_id = str(probe_id)
        if name is None:
            self.name = str(probe_id)
        else:
            self.name = name
        self.master = master
    
    def __str__(self):
        prefix = ', secondary probe'        
        if self.master:
            prefix = ', master probe'
        return 'Probe #' + self.probe_id + ', name: ' + self.name + prefix 

def _get_new_timestamp():
    """ gets a new timestamp as an integer """
    return int(time.time())

class TemperatureReading():
    """ represents a single temperature probe reading from a moment in time """            
    def __init__(self, probe_id, temperature_C, timestamp=None):
        self.probe_id = str(probe_id)
        self.temperature_C = temperature_C
        self.temperature_F = temperature_C * 9.0 / 5.0 + 32.0
        if timestamp is None:
            self.timestamp = _get_new_timestamp()
        else:
            self.timestamp = int(timestamp)
                                                                
    def __str__(self):
        pretty_date = misc_utils.timestamp_to_datetime(self.timestamp).strftime("%c")
        return 'From probe #' + self.probe_id + ': ' + str(self.temperature_C) + 'C/' + str(self.temperature_F) + 'F. Taken at: ' + pretty_date + "."

def read_temp_raw(device_file):
    """ uses cat to read the file """
    catdata = subprocess.Popen(['cat', device_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = catdata.communicate()  # @UnusedVariable
    out_decode = out.decode('utf-8')
    lines = out_decode.split('\n')
    return lines

def initialize_probes():
    """ looks for existing probes in the /sys folder and writes their ids to the database """
    global probe_ids     
    if chestfreezer_gpio.using_real_pi:   
        for device_folder in glob.glob(TEMPERATURE_PROBE_PATH + '28*'):        
            probe_id = device_folder.split('28-', 1)[1]        
            probe_id_pruned = str(probe_id[5:])            
            probe_ids.append(probe_id_pruned)
    else:  
        probe_ids.append(test_data.PROBE1_ID)
        probe_ids.append(test_data.PROBE2_ID)
        probe_ids.append(test_data.PROBE3_ID)
    
    for probe_id in probe_ids:
        probe = Probe(probe_id)
        database.db_adapter.store_probe(probe, False)

def get_temperature_readings():
    """ reads (immediately) the temperature readings from the probes returns a list with any temperature read """
    readings = []
    if chestfreezer_gpio.using_real_pi:
        for probe_id in probe_ids:        
            device_file = TEMPERATURE_PROBE_PATH + '28-00000' + probe_id + '/w1_slave'                    
            lines = read_temp_raw(device_file)
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = read_temp_raw(device_file)
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos + 2:]
                temperature_C = float(temp_string) / 1000.0            
                reading = TemperatureReading(probe_id, temperature_C)
                readings.append(reading)
                if probe_id == master_probe_id:
                    global last_master_reading
                    last_master_reading = reading
    else:
        for probe_id in probe_ids:                        
            reading = test_data.get_temperature_for_probe(probe_id)
            readings.append(reading)
    return readings        

def determine_master_probe():
    """ if there is no temperature probe set as the MASTER one, will set the first one """    
    first_result = None
    is_anyone_master = False
    for probe in database.db_adapter.get_all_probes():
        if first_result is None:
            first_result = probe
        if probe.master == 1:
            is_anyone_master = True
            break    
    if not is_anyone_master:
        first_result.master = True 
        database.db_adapter.store_probe(first_result)
        master_probe_id = first_result.probe_id
        print 'Auto-determined probe #' + str(first_result.probe_id) + ' to be the master one.' 

def set_probe_as_not_master(probe_id):
    """ removes the master status from the given probe, if any """
    probe = database.db_adapter.get_probe_by_id(probe_id)
    if probe.master:        
        probe.master = False
        master_probe_id = None
        database.db_adapter.store_probe(probe)    
    
def set_probe_as_master(probe_id):
    """ sets the given probe to Master, and all the other ones to not-master """
    found = False
    for probe in database.db_adapter.get_all_probes():
        if probe.probe_id == probe_id:
            probe.master = True
            database.db_adapter.store_probe(probe)
            found = True
        else:
            probe.master = False
            database.db_adapter.store_probe(probe)            
    if not found:
        determine_master_probe()                
        raise Exception('Could not find probe #' + probe_id + ', no update done.')

def get_master_probe():
    """ returns the probe set to master """
    for probe in database.db_adapter.get_all_probes():
        if probe.master:
            return probe

def set_probe_name(probe_id, new_name):
    """ changes the probe's name """
    for probe in  database.db_adapter.get_all_probes():
        if probe.probe_id == probe_id:
            probe.name = new_name
            database.db_adapter.store_probe(probe)
            return
    raise Exception('Could not find probe #' + probe_id + ', no update done.')

def start_temperature_recording_thread():
    """ recods all the temp readings from the probes every X seconds """
    def record_temperatures():        
        while True:        
            try:
                readings = get_temperature_readings()               
                if readings is not None:
                    database.db_adapter.store_temperatures(readings)           
            except Exception as e:
                print 'Could not log temperature. Error:\n' + str(e)
            time.sleep(configuration.store_temperature_interval_seconds())
    temperature_recording_thread = Thread(target=record_temperatures, args=())
    temperature_recording_thread.daemon = True
    temperature_recording_thread.start()

