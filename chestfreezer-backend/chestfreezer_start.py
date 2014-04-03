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

def checkImports():
    try:
        __import__('RPi')
        try: 
            import RPi.GPIO  # @UnusedImport
        except RuntimeError:
            raise ImportError()
    except ImportError:
        sys.exit('Either you are not using a raspberry pi or you don\'t have RPi installed.\nTry visiting https://pypi.python.org/pypi/RPi.GPIO')
    print 'Installed libraries and modules are all place.'        

def do_sound_check():
    """ asks the user if he heard 4 clicks, returns the boolean result"""
    print 'Did you hear the four distinct clicking noises (enter \'y\' or \'n\' or any other key to repeat)?'
    response = misc_utils.get_single_char().lower()
    if response == 'y':
        return True
    elif response == 'n':
        sys.exit('There seems to be a pin connectivity problem, check your wiring. Terminating.')
    else:
        return False    

def checkHardware():
    # first the GPIO pins
    import hardware.chestfreezer_gpio as gpio
    sound_check_passed = False;
    while not sound_check_passed:
        print 'Checking plug control - you should hear four distinct clicking noises...'
        try:  
            gpio.output_pin_for_time(configuration.device1_pin(), False, 1)
            gpio.output_pin_for_time(configuration.device2_pin(), False, 1)
        except ValueError as e:
            gpio.cleanup()
            sys.exit('Pins could not be activated, reason:\n' + str(e) + '\nTerminating.')
        sound_check_passed = do_sound_check()            
    print 'Pins #' + configuration.device1_pin() + ' and #' + configuration.device2_pin() + '  are connected correctly.'            
    
    # then the temperature sensor(s)
    print temperature.getTemperatureReadings()
        
def checkInternetConnectivity():    
    try:
        urllib2.urlopen('http://74.125.228.100', timeout=1)
        do_we_have_internet = True
    except urllib2.URLError:
        do_we_have_internet = False        
    if do_we_have_internet:
        print 'Internet connection is working fine.'
    else:
        print 'Could not reach the internet. If you want to proceed regardless then press \'y\', otherwise press any other key to exit.'
        response = misc_utils.get_single_char().lower()
        if response != 'y':
            sys.exit('Terminating.')        

def checkDatabase():
    try:
        mysql_adapter.connect()        
        print 'Successfully connected to database.'
    except Exception as e:
        sys.exit('Could not connect to database. Error:\n' + str(e) + '\nTerminating.')
            
def startTemperatureRecordingThread():
    pass

def startControllerThread():
    pass

def startWebInterface():
    pass


if __name__ == "__main__":    
    # check if everything is in place
    checkImports()
    checkHardware()
    checkInternetConnectivity()
    checkDatabase()
    
    # start threads that do all the work
    startTemperatureRecordingThread()
    startControllerThread()
    
    # finally, the web interface
    startWebInterface()

    
