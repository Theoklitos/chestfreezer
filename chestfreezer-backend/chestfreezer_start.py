'''
Created on Apr 2, 2014

Top level module that is responsible for initializing everything

@author: theoklitos
'''

import sys
import urllib2
from util import configuration, misc_utils
from hardware import temperature
from database import mysql_adapter
import time
from threading import Thread

def checkImports():
    try:
        __import__('RPi')
        try: 
            import RPi.GPIO  # @UnusedImport
        except RuntimeError:
            raise ImportError()
    except ImportError:
        sys.exit('Either you are not using a raspberry pi or you don\'t have RPi installed.\nTry visiting https://pypi.python.org/pypi/RPi.GPIO')
    try:
        __import__('api')
    except ImportError:
        sys.exit('You need to install api.py. Try visiting http://webpy.org/install')
    print 'Installed libraries and modules are all place.'        

def do_sound_check(gpio):
    """ asks the user if he heard 4 clicks, returns the boolean result"""
    print 'Did you hear the four distinct noises (enter \'y\' or \'n\' or any other key to repeat)?'
    response = misc_utils.get_single_char().lower()
    if response == 'y':
        return True
    elif response == 'n':
        gpio.cleanup()        
        sys.exit('There seems to be a pin connectivity problem, check your wiring. Terminating.')
    else:
        return False    

def checkHardware():
    # first the GPIO pins
    import hardware.chestfreezer_gpio as gpio    
    sound_check_passed = False;
    while not sound_check_passed:
        print 'Checking device control - you should hear four clicking noises...'
        time.sleep(1)
        try:  
            gpio.output_pin_for_time(configuration.heater_pin(), False, 1)
            time.sleep(1)
            gpio.output_pin_for_time(configuration.freezer_pin(), False, 1)
        except ValueError as e:            
            sys.exit('Pins could not be activated, reason:\n' + str(e) + '\nTerminating.')
        sound_check_passed = do_sound_check(gpio)            
    print 'GPIO pins #' + configuration.heater_pin() + ' and #' + configuration.freezer_pin() + ' connected correctly.'            
    
    # then the temperature sensor(s)
    temperature.initialize_probes()
    probes = temperature.probe_ids        
    if probes is None:    
        sys.exit('No temperature probes were detected, check your wiring. Terminating.')
    else:
        print 'Found ' + str(len(probes)) + ' functional temperature sensor(s).'
        mysql_adapter.determine_master_probe()            

def checkInternetConnectivity():    
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

def checkAndInitDatabase():
    try:
        mysql_adapter.connect()
        print 'Successfully connected to the database.'
    except Exception as e:
        sys.exit('Could not connect to database. Error:\n' + str(e) + '\nTerminating.')
            
def startTemperatureRecordingThread():
    """ starts a thread that stored the temperature readings every second """
    def record_temperatures():        
        while True:        
            try:
                mysql_adapter.store_temperatures(temperature.get_temperature_readings())                
            except Exception as e:
                print 'Could not log temperature. Error:\n' + str(e)
            time.sleep(configuration.store_temperature_interval_seconds())
    temperature_recording_thread = Thread(target=record_temperatures, args=())
    temperature_recording_thread.start()

def startControllerThread():
    pass

def startWebInterface():    
    import api.chestfreezer_api as api
    print 'Starting web interface...\n'
    api.run()    

if __name__ == "__main__":
    # check if everything is in place
    checkImports()
    checkAndInitDatabase()
    checkHardware()
    checkInternetConnectivity()    
    
    # start threads that do all the work
    startTemperatureRecordingThread()
    startControllerThread()
    
    # finally, the api interface
    startWebInterface()

    
