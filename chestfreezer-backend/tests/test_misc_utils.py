'''
Created on Apr 10, 2014

Tests for the misc_utils

@author: theoklitos
'''

import unittest
from util import misc_utils
import datetime

class TestMiscUtils(unittest.TestCase):    
        
    def test_is_within_distance(self):
        assert(misc_utils.is_within_distance(10, 15, 6))
        assert(misc_utils.is_within_distance(1, 1.5, 0.6))
        assert(misc_utils.is_within_distance(10, 20, 10))
        assert(misc_utils.is_within_distance(100, -100, 200))
        assert(misc_utils.is_within_distance(10, 10.5, 0.5))
        
        assert(not misc_utils.is_within_distance(65, 72.3, 0.5))
        assert(not misc_utils.is_within_distance(1, 2, 0.5))
        assert(not misc_utils.is_within_distance(30, 60, 29))
        assert(not misc_utils.is_within_distance(0.5, -1, 0.1))
    
    def test_temperature_conversion(self):
        original_C = 25.5
        f = misc_utils.celsius_to_fahrenheit(original_C)        
        back_to_C = misc_utils.fahrenheit_to_celsius(f)        
        assert(str(original_C) == str(back_to_C))
        
        original_F = 93.2
        c = misc_utils.fahrenheit_to_celsius(original_F)
        back_to_F = misc_utils.celsius_to_fahrenheit(c)
        assert(original_F == back_to_F)
        
    def test_get_start_end_of_day(self):
        a_datetime = datetime.datetime(2014,01,31,17,33,12).strftime("%s")        
        results = misc_utils.get_start_and_end_of_day(a_datetime)
        # hardcoded values that are known to be correct
        assert results[0] == 1391122800
        assert results[1] == 1391209199
            
if __name__ == '__main__':
    unittest.main()