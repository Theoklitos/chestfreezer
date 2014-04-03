'''
Created on Apr 2, 2014

Initializes and takes readings from the temperature sensors

@author: theoklitos
'''

import glob
import subprocess
import time
import datetime

TEMPERATURE_PROBE_PATH = '/sys/bus/w1/devices' 

class TempReading():
    """ represents a single temp probe reading from a moment in time """            
    def __self__(self, probe_id, temperature_C, temperature_F, timestamp):
        self.probe_id = probe_id
        self.temperature_C = temperature_C
        self.temperature_F = temperature_F
        self.timestamp = timestamp
        
    def __str__(self):
        #pretty_date = self.timestamp.strftime("%A %w, %y")
        pretty_date = self.timestamp.strftime("%c")
        return 'From probe #' + self.probe_id + ': ' + self.temperature_C + 'C /' + self.temperature_F + 'F. Taken at: ' + pretty_date + "."

def read_temp_raw(device_file):
    """ uses cat to read the file """
    catdata = subprocess.Popen(['cat',device_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = catdata.communicate()  # @UnusedVariable
    out_decode = out.decode('utf-8')
    lines = out_decode.split('\n')
    return lines

def getTemperatureReadings():
    """ reads (immediately) the temperature readings from the probes returns a list with any temperature read """
    readings = []    
    for device_folder in glob.glob(TEMPERATURE_PROBE_PATH + '28*'):
        print '\nDEVICE FOLDER!: ' + device_folder + '\n'            
        device_file = device_folder + '/w1_slave'
        probe_id = device_folder.split('28-',1)[1]        
        lines = read_temp_raw(device_file)
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temperature_C = float(temp_string) / 1000.0
            temperature_F = temperature_C * 9.0 / 5.0 + 32.0
            reading = TempReading(probe_id, temperature_C, temperature_F,datetime.datetime.now())
            readings.append(reading)
        return readings        
        
