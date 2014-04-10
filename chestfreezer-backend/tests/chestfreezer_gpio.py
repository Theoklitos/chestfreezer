'''
Created on Apr 7, 2014

Tests for the GPIO module

@author: theoklitos
'''
import unittest
from hardware import chestfreezer_gpio
from mock import Mock

class TestChestfreezerGPIO(unittest.TestCase):    
        
    def setUp(self):
        chestfreezer_gpio.using_real_pi = True
        
    def test_check_output_pin(self):
        chestfreezer_gpio.GPIO.setup = Mock()
        chestfreezer_gpio.GPIO.output = Mock()        
        chestfreezer_gpio.output_pin(1, False)
                
        chestfreezer_gpio.GPIO.setup.assert_called_once_with(1, chestfreezer_gpio.GPIO.OUT) # @UndefinedVariable
        chestfreezer_gpio.GPIO.output.assert_called_once_with(1, False) # @UndefinedVariable
    
    def test_output_pin_for_time(self):
        chestfreezer_gpio.GPIO.setup = Mock()
        chestfreezer_gpio.GPIO.output = Mock()        
        chestfreezer_gpio.output_pin_for_time(1, False, 1)
                
        chestfreezer_gpio.GPIO.setup.assert_called_once_with(1, chestfreezer_gpio.GPIO.OUT) # @UndefinedVariable
        chestfreezer_gpio.GPIO.output.assert_any_call(1, False) # @UndefinedVariable
        chestfreezer_gpio.GPIO.output.assert_any_call(1, True) # @UndefinedVariable
    
    def test_cleanup(self):
        chestfreezer_gpio.GPIO.cleanup = Mock()        
        chestfreezer_gpio.cleanup()
        
        chestfreezer_gpio.GPIO.cleanup.assert_called_once_with() # @UndefinedVariable

if __name__ == '__main__':
    unittest.main()
