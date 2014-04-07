'''
Created on Apr 6, 2014

Testing for the initializing chestfreezer_start module

@author: theoklitos
'''
import unittest
from bin import chestfreezer_start
from mock import Mock

def overwriten_db_type():
    return 'memory'

class TestChestfreezerStartup(unittest.TestCase):    
    
    def setUp(self):
        chestfreezer_start.configuration.db_type = overwriten_db_type
        
    def test_check_and_init_database(self):        
        chestfreezer_start.db_adapter.connect = Mock()
        chestfreezer_start.check_and_init_database()  
                              
        chestfreezer_start.db_adapter.connect.assert_called_once_with()  # @UndefinedVariable 
        
    def test_check_hardware(self):
        chestfreezer_start.db_adapter.connect = Mock()
        chestfreezer_start.chestfreezer_gpio.output_pin_for_time = Mock()
        chestfreezer_start.temperature_probes.initialize_probe = Mock()
        chestfreezer_start.temperature_probes.determine_master_probe = Mock()
        chestfreezer_start.db_adapter.store_probe = Mock()                
        chestfreezer_start.check_hardware()        
        
        chestfreezer_start.chestfreezer_gpio.output_pin_for_time.assert_any_call('5', False, 1) # @UndefinedVariable
        chestfreezer_start.chestfreezer_gpio.output_pin_for_time.assert_any_call('3', False, 1) # @UndefinedVariable                
    
    def test_check_internet_connectivity(self):
        chestfreezer_start.urllib2.urlopen = Mock()
        chestfreezer_start.check_internet_connectivity()
        
        chestfreezer_start.urllib2.urlopen.assert_called_once_with('http://74.125.228.100', timeout=5) # @UndefinedVariable
    
    def test_start_threads(self):
        pass
    
    def test_start_web_interface(self):   
        pass

if __name__ == '__main__':
    unittest.main()
