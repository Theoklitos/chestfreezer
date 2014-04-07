'''
Created on Apr 7, 2014

Dummy implementation of RPi.GPIO that does nothing but print log statements

@author: theoklitos
'''
from util import misc_utils

BOARD = 'BOARD'
OUT = 'OUT'

def setwarnings(should_set_warning):
    print '[Dummy HW Mode] Show warnings set to: ' + str(should_set_warning)

def setmode(mode):
    print '[Dummy HW Mode] Setting board to mode "' + str(mode) + "'"
    
def setup(pin_number, mode):
    print '[Dummy HW Mode] Setting pin #' + str(pin_number) + ' to mode "' + mode + "'"    

def output(pin_number, state):
    print '[Dummy HW Mode] Setting pin #' + str(pin_number) + ' to state: ' + misc_utils.boolean_to_readable_string(state)

def cleanup():
    print '[Dummy HW Mode] Call to cleanup the GPIO pins'