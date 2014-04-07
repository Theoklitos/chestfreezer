'''
Created on Apr 7, 2014

Test for the bottle.py based API. This is more of a functional than a unit test.

@author: theoklitos
'''

import unittest
import httplib2
from api import chestfreezer_api
import time
from database import db_adapter
from tests import test_data
from hardware import temperature_probes
import json

def overwriten_db_type():
    return 'memory'
    
class TestChestfreezerAPI(unittest.TestCase):    
        
    def _do_GET_with_credentials(self, url, username='test_username', password='test_password'):
        """ performs a GET with basic auth """
        self.http.add_credentials(username, password)
        return self.http.request(url, "GET")
    
    @classmethod
    def setUpClass(self):
        chestfreezer_api.start()
        time.sleep(1)                
        chestfreezer_api.configuration.db_type = overwriten_db_type
        chestfreezer_api.configuration.set_should_send_emails(False)
        chestfreezer_api.configuration.set_is_security_enabled(False)        
        db_adapter.connect()        
        temperature_probes.initialize_probes()        
        self.http = httplib2.Http(".cache")  
        print       
        
    def setUp(self):
        print '========================== Starting test case ========================'
    
    def test_get_temperatures(self):
        """ gets all the temperatures """
        test_data.insert_test_temperatures(10)        
        response, content = self._do_GET_with_credentials('http://localhost:8080/chestfreezer/api/temperature')         
        assert(response.status == 200)        
        data = json.loads(content)
        assert(len(data) == 30)
    
    def test_get_temperatures_for_timestamps(self):
        """ asks for temperatures within time bounds """
        test_data.insert_test_temperatures(20)
        startMillis = str(int(time.time()) - 70) #a little over a  minute ago        
        endMillis = str(int(time.time()))
        response, content = self._do_GET_with_credentials('http://localhost:8080/chestfreezer/api/temperature?start=' + startMillis + '&end=' + endMillis)        
        assert(response.status == 200)                
        data = json.loads(content)
        assert(len(data) == 6)
        
    def tearDown(self):
        # bad way of terminating the thread
        chestfreezer_api.db_adapter.drop_tables()
        chestfreezer_api.db_adapter.initialize_tables()
        print '==================== Cleared DB and ended test case ==================\n'
        
    
