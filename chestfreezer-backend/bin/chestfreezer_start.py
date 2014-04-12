'''
Created on Apr 2, 2014

Top level module that is responsible for initializing everything

@author: theoklitos
'''
# begin with some package checks
import sys
import os
sys.path.append(os.path.abspath('..'))
from util import configuration, misc_utils

__import__('hardware.chestfreezer_gpio')
try:
    __import__('api')
except ImportError:
    sys.exit('You don\'t have bottle.py installed. Try apt-get install python-bottle')    
if configuration.db_type() == configuration.DATABASE_IN_DISK_CONFIG_VALUE:
    try:
        __import__('MySQLdb')
    except ImportError:
        sys.exit('You don\'t have the python mysql connector installed. Try apt-get install python-mysqldb')

import urllib2
from hardware import chestfreezer_gpio, temperature_probes
from database import db_adapter
import time
import termios
from tests import test_data
import control.brew_logic as logic
import api.chestfreezer_api as api

def do_sound_check():
    """ asks the user if he heard 4 clicks, returns the boolean result"""
    print 'Did you hear the four distinct noises (enter \'y\' or \'n\' or any other key to repeat)?'
    response = misc_utils.get_single_char().lower()
    if response == 'y':
        return True
    elif response == 'n':
        chestfreezer_gpio.cleanup()        
        sys.exit('There seems to be a pin connectivity problem, check your wiring. Terminating.')
    else:
        return False    

def check_hardware():    
    # first the GPIO pins        
    sound_check_passed = 'skip-gpio-test' in sys.argv;
    while not sound_check_passed:
        print 'Checking device control - you should hear four clicking noises...'
        time.sleep(1)
        try:
            chestfreezer_gpio.output_pin_for_time(configuration.heater_pin(), False, 1)            
            time.sleep(1)                        
            chestfreezer_gpio.output_pin_for_time(configuration.freezer_pin(), False, 1)
        except ValueError as e:            
            sys.exit('Pins could not be activated, reason:\n' + str(e) + '\nTerminating.')
        try:
            # eclipse cannot handle this!
            sound_check_passed = do_sound_check()
        except termios.error:
            print 'You are using eclipse or some other IDE, check passed.'
            sound_check_passed = True  
    print 'GPIO pins #' + configuration.heater_pin() + ' and #' + configuration.freezer_pin() + ' connected correctly.'            
    
    # then the temperature sensor(s)
    temperature_probes.initialize_probes()
    probes = temperature_probes.probe_ids        
    if probes is None:    
        sys.exit('No temperature probes were detected, check your wiring. Terminating.')
    else:
        print 'Found ' + str(len(probes)) + ' functional temperature sensor(s).'
        temperature_probes.determine_master_probe()
        if 'insert-test-data' in sys.argv:                        
            test_data.insert_test_temperatures()                

def check_internet_connectivity():    
    print 'Checking internet connectivity...',
    try:
        urllib2.urlopen('http://74.125.228.100', timeout=5)  # ping google
        do_we_have_internet = True
    except urllib2.URLError:
        do_we_have_internet = False        
    if do_we_have_internet:
        print 'connection is good.'
    else:
        print '\nCould not reach the internet. If you want to proceed regardless then press \'y\', otherwise press any other key to exit.'
        response = misc_utils.get_single_char().lower()
        if response != 'y':
            sys.exit('Terminating.')        

def check_and_init_database():    
    try:
        db_adapter.connect()
        print 'Successfully connected to the database.'
    except Exception as e:
        sys.exit('Could not connect to database. Error:\n' + str(e) + '\nTerminating.')
            
def start_threads():
    """ starts a thread that stored the temperature readings every second, and the other 2 temperature controlling threads """
    temperature_probes.start_temperature_recording_thread()
    logic.start_instruction_thread()
    logic.start_temperature_control_thread()

def start_web_interface():        
    """ starts the bottle.py server """            
    print 'Starting web interface...\n'        
    api.start()
        
if __name__ == "__main__":
    check_and_init_database()     
    check_hardware()
    check_internet_connectivity()    
    start_threads()
    start_web_interface()
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print '\nInterrupted, shutting down...'
        # stop threads, cleanup, etc? TODO
        chestfreezer_gpio.cleanup()
        sys.exit("Goodbye!")
    except Exception as e:
        print 'Exception: ' + str(e)
        
