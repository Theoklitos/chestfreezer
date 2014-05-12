'''
Created on May 1, 2014

custom testrunner to run all the tests

@author: theoklitos
'''
import unittest
from tests.test_brew_logic import TestBrewLogic
from tests.test_chestfreezer_api import TestChestfreezerAPI
from tests.test_chestfreezer_gpio import TestChestfreezerGPIO
from tests.test_db_adapter import TestDatabaseAdapter
from tests.test_chestfreezer_start import TestChestfreezerStart
from tests.test_configuration import TestConfiguration
from tests.test_misc_utils import TestMiscUtils
from tests.test_temperature_probes import TestTemperatureProbes

if __name__ == '__main__':
    all_tests = [];
    all_tests.append(unittest.TestLoader().loadTestsFromTestCase(TestBrewLogic))
    all_tests.append(unittest.TestLoader().loadTestsFromTestCase(TestChestfreezerAPI))
    all_tests.append(unittest.TestLoader().loadTestsFromTestCase(TestChestfreezerGPIO))
    all_tests.append(unittest.TestLoader().loadTestsFromTestCase(TestDatabaseAdapter))
    all_tests.append(unittest.TestLoader().loadTestsFromTestCase(TestChestfreezerStart))
    all_tests.append(unittest.TestLoader().loadTestsFromTestCase(TestConfiguration))
    all_tests.append(unittest.TestLoader().loadTestsFromTestCase(TestMiscUtils))
    all_tests.append(unittest.TestLoader().loadTestsFromTestCase(TestTemperatureProbes))
    
    all_tests = unittest.TestSuite(all_tests);    
    runner=unittest.TextTestRunner()    
    #runner.run(all_tests)
    runner.run(unittest.TestLoader().loadTestsFromTestCase(TestBrewLogic))
    runner.run(unittest.TestLoader().loadTestsFromTestCase(TestChestfreezerAPI))
    runner.run(unittest.TestLoader().loadTestsFromTestCase(TestChestfreezerGPIO))
    runner.run(unittest.TestLoader().loadTestsFromTestCase(TestDatabaseAdapter))
    runner.run(unittest.TestLoader().loadTestsFromTestCase(TestChestfreezerStart))