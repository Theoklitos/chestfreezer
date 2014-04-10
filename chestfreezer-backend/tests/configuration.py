'''
Created on Apr 7, 2014

Tests for the the configuration

@author: theoklitos
'''
import unittest
from util import configuration
from mock import Mock

class TestConfiguration(unittest.TestCase):    
        
    def test_is_IP_allowed(self):
        configuration._get_option_with_default = Mock()
        configuration._get_option_with_default.return_value = '666.666.666.666 , 192.168.0.1, 5.4.3.1'
        assert(configuration.is_ip_allowed('666.666.666.666'))
        assert(not configuration.is_ip_allowed('999.999.999.999'))        
    
    def test_is_IP_allowed_nothing_in_config_file(self):
        """ when there is no IP specified in the file, all IPs should be allowed """
        configuration._get_option_with_default = Mock()
        configuration._get_option_with_default.return_value = '   '
        assert(configuration.is_ip_allowed('666.666.666.666'))
        assert(configuration.is_ip_allowed('999.999.999.999'))
        
if __name__ == '__main__':
    unittest.main()
