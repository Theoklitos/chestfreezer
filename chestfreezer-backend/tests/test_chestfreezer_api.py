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
from util import data_for_testing, configuration
from hardware import temperature_probes
import json
from control import brew_logic
import base64
from control.brew_logic import Instruction

def overwriten_db_type():
    return 'memory'
    
class TestChestfreezerAPI(unittest.TestCase):    
    
    def _call_method_with_credentials_and_body(self, url, method_name, body=None, content_type=None, username='test-username', password='test-password'):
        """ basic function used to call methods with various parameters """
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')        
        return self.http.request(url, method_name.upper(), body, headers={'Authorization':'Basic %s' % base64string, 'Content-Type':content_type})        
    
    def _call_GET_with_credentials(self, url, username='test-username', password='test-password'):
        """ performs a GET with basic auth """
        return self._call_method_with_credentials_and_body(url, 'GET', username, password)        
    
    def _call_DELETE_with_credentials(self, url, username='test-username', password='test-password'):
        """ performs a DELETE with basic auth """
        return self._call_method_with_credentials_and_body(url, 'DELETE', username, password)                
    
    def _call_POST_with_credentials_and_body(self, url, body, content_type, username='test-username', password='test-password'):
        """ performs a POST with basic auth and the given method payload/body """
        # note: use either application/x-www-form-urlencoded or application/json
        return self._call_method_with_credentials_and_body(url, 'POST', body, content_type, username, password)
        
    def _call_PUT_with_credentials_and_body(self, url, body, content_type, username='test-username', password='test-password'):
        """ performs a PUT with basic auth and the given method payload/body """
        # note: use either application/x-www-form-urlencoded or application/json
        return self._call_method_with_credentials_and_body(url, 'PUT', body, content_type, username, password)               
  
    def _call_POST_device_state_with_content(self, turn_on_body, turn_off_body, header):
        """ switches the device state on and off with the given post bodies and header """
        response = self._call_POST_with_credentials_and_body('http://localhost:8080/chestfreezer/api/device/freezer', turn_on_body, header)[0]
        assert(response.status == 204) | (response.status == 200)
        assert(brew_logic.freezer_state)
        assert(brew_logic.freezer_override)
        response = self._call_POST_with_credentials_and_body('http://localhost:8080/chestfreezer/api/device/freezer', turn_off_body, header)[0]
        assert(not brew_logic.freezer_state)
        assert(brew_logic.freezer_override)
        
    @classmethod
    def setUpClass(self):
        chestfreezer_api.start(server_type = "wsgiref")
        time.sleep(1)                
        chestfreezer_api.configuration.db_type = overwriten_db_type        
        chestfreezer_api.configuration.set_should_send_emails(False)
        chestfreezer_api.configuration.set_is_security_enabled(True)        
        db_adapter.connect()        
        temperature_probes.initialize_probes()        
        temperature_probes.determine_master_probe()
        self.http = httplib2.Http(".cache")
        print       
            
    def setUp(self):
        chestfreezer_api.db_adapter.drop_tables(False)
        chestfreezer_api.db_adapter.initialize_tables()                
        print '========================== Starting test case ========================'
    
    def test_get_device_state(self):
        brew_logic.set_freezer_override(True)        
        response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/device')
        assert(response.status == 200)        
        data = json.loads(content)
        assert(data.get('heater').get('state') == 'off')        
        assert(data.get('heater').get('overridden') == 'false')
        assert(data.get('freezer').get('state') == 'on')        
        assert(data.get('freezer').get('overridden') == 'true')
        brew_logic.set_freezer_override(False)
        brew_logic.set_heater_override(True)
        response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/device')
        assert(response.status == 200)        
        data = json.loads(content)
        assert(data.get('heater').get('state') == 'on')        
        assert(data.get('heater').get('overridden') == 'true')
        assert(data.get('freezer').get('state') == 'off')        
        assert(data.get('freezer').get('overridden') == 'true')
        
    def test_set_device_state_form(self):
        self._call_POST_device_state_with_content('state=on', 'state=OFF', 'application/x-www-form-urlencoded')
        
    def test_set_device_state_json(self):
        self._call_POST_device_state_with_content('{"state":"on"}', '{"state":"Off"}', 'application/json')        
    
    def test_set_probe_name(self):         
        second_probe_id = temperature_probes.probe_ids[0]
        response = self._call_PUT_with_credentials_and_body('http://localhost:8080/chestfreezer/api/probe/' + second_probe_id, '{"name":"new_name", "master":"true"}', 'application/json')[0]
        assert(response.status == 204)
        assert(db_adapter.get_probe_by_id(second_probe_id).name == 'new_name')

    def test_set_probe_master(self):
        response = self._call_PUT_with_credentials_and_body('http://localhost:8080/chestfreezer/api/probe/' + str(temperature_probes.master_probe_id), '{"master":"false"}', 'application/json')[0]
        assert(response.status == 204)
        assert(not temperature_probes.master_probe_id)
        new_master_probe_id = str(temperature_probes.probe_ids[2])
        response = self._call_PUT_with_credentials_and_body('http://localhost:8080/chestfreezer/api/probe/' + new_master_probe_id, '{"master":"TRUE"}', 'application/json')[0]
        assert(response.status == 204)
        assert(temperature_probes.master_probe_id == new_master_probe_id)
        assert(db_adapter.get_probe_by_id(new_master_probe_id).master)        
        
    def test_get_probes(self):
        response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/probe')
        assert(response.status == 200)
        data = json.loads(content)    
        assert(len(data) == 3)
        for probe_id in temperature_probes.probe_ids:
            response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/probe/' + str(probe_id))
            assert(response.status == 200)
            data = json.loads(content)    
            assert(len(data) == 3)
            assert(data.get('probe_id') == probe_id)        
            
    def test_create_instruction(self):        
        json = '{ "description" : "Instruction created from web API", "target_temperature_C" : "15.5", "from_timestamp" : "10", "to_timestamp" : "1000" }'        
        response = self._call_POST_with_credentials_and_body('http://localhost:8080/chestfreezer/api/instruction', json, 'application/json')[0]
        assert(response.status == 201)
        assert(len(db_adapter.get_all_instructions()) == 1)
        new_instruction = db_adapter.get_all_instructions()[0]
        assert(new_instruction.target_temperature_C == 15.5)
        assert(new_instruction.from_timestamp == 10)        
        assert(new_instruction.description == 'Instruction created from web API')
            
    def test_modify_instruction(self):
        instruction = Instruction(1, 99, 1, time.time() - 200)
        brew_logic.store_instruction_for_unique_time(instruction)        
        json = '{ "description" : "modified description", "target_temperature_C" : "15.5", "from_timestamp" : "1000"}'        
        response = self._call_PUT_with_credentials_and_body('http://localhost:8080/chestfreezer/api/instruction/1', json, 'application/json')[0]
        assert(response.status == 204)        
        assert(db_adapter.get_instruction_by_id('1').from_timestamp == 1000)
        assert(db_adapter.get_instruction_by_id('1').description == 'modified description')
        assert(db_adapter.get_instruction_by_id('1').target_temperature_C == 15.5)
        
    def test_set_temperature_directly_C(self):
        response = self._call_POST_with_credentials_and_body('http://localhost:8080/chestfreezer/api/temperature/target', '{"target_temperature_C": 66.6}', 'application/json')[0]
        assert(response.status == 204)
        assert(brew_logic.temperature_override_C == 66.6)
        response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/temperature/target')
        assert(response.status == 200)
        data = json.loads(content)
        assert(str(data.get('target_temperature_C')) == '66.6')
        
    def test_set_temperature_directly_F(self):
        response = self._call_POST_with_credentials_and_body('http://localhost:8080/chestfreezer/api/temperature/target', 'target_temperature_F=120.2', 'application/x-www-form-urlencoded')[0]
        assert(response.status == 204)        
        assert(str(brew_logic.temperature_override_C) == '49.0')
        response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/temperature/target')
        assert(response.status == 200)
        data = json.loads(content)        
        assert(str(data.get('target_temperature_C')) == '49.0')         
        assert(str(data.get('target_temperature_F')) == '120.2')
    
    def test_set_and_remove_device_override(self):
        """ when the brew logic is handling the device and we override it, after we remove the override it should continue doing what it was """
        brew_logic.configuration.set_instruction_interval_seconds(0.1)
        brew_logic.configuration.set_control_temperature_interval_seconds(0.5)  
        brew_logic.start_instruction_thread()
        brew_logic.start_temperature_control_thread()        
        json = '{ "description" : "Instruction created from web API", "target_temperature_C" : "15.5", "from_timestamp" : "10", "to_timestamp" : "2397162478" }'        
        response = self._call_POST_with_credentials_and_body('http://localhost:8080/chestfreezer/api/instruction', json, 'application/json')[0]
        assert(response.status == 201)
        time.sleep(0.5)
        # the instruction takes over
        assert(brew_logic.get_actual_target_temperature_C() == 15.5)
        # we manually override
        response = self._call_POST_with_credentials_and_body('http://localhost:8080/chestfreezer/api/temperature/target', '{"target_temperature_C": -5.1}', 'application/json')[0]
        assert(response.status == 204)
        time.sleep(0.5)
        assert(brew_logic.get_actual_target_temperature_C() == -5.1)
        # we remove our override
        time.sleep(0.5) 
        response = self._call_POST_with_credentials_and_body('http://localhost:8080/chestfreezer/api/temperature/target', '{"override": "false" }', 'application/json')[0]
        assert(response.status == 204)
        # the instruction temperature should be used again
        time.sleep(0.5)         
        assert(brew_logic.get_actual_target_temperature_C() == 15.5)
    
    def test_get_instructions(self):
        instruction1 = Instruction(1, 15, time.time() - 600, time.time() - 100, 'Test instruction 15C')
        instruction2 = Instruction(2, 0, time.time() - 1200, time.time() - 600, 'Test instruction 0C')
        instruction3 = Instruction(3, 7, time.time() - 50, time.time() + 2000, 'Test instruction 7C')
        brew_logic.store_instruction_for_unique_time(instruction1)
        brew_logic.store_instruction_for_unique_time(instruction2)
        brew_logic.store_instruction_for_unique_time(instruction3)
        response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/instruction')
        assert(response.status == 200)
        data = json.loads(content)        
        assert(len(data) == 3)
        response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/instruction?now')
        assert(response.status == 200)        
        data = json.loads(content)                        
        assert(len(data) == 5)  # its not a list, its one element / 5 fields
        assert(data.get('instruction_id') == instruction3.instruction_id)
        start = str(int(time.time() - 1000))
        end = str(int(time.time() - 200))
        response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/instruction?start=' + start + '&end=' + end)        
        assert(response.status == 200)
        data = json.loads(content)
        assert(len(data) == 2)
        assert(data[0].get('instruction_id') == instruction1.instruction_id)
        assert(data[1].get('instruction_id') == instruction2.instruction_id)
    
    def test_delete_instruction(self):
        instruction = Instruction(1, 15, time.time() - 600, time.time() + 6000, 'Bla bla')
        brew_logic.store_instruction_for_unique_time(instruction)        
        response = self._call_DELETE_with_credentials('http://localhost:8080/chestfreezer/api/instruction/1')[0]
        assert(response.status == 204)        
        assert(len(db_adapter.get_all_instructions()) == 0)        
    
    def test_get_temperatures(self):
        """ gets all the temperatures """
        data_for_testing.insert_dummy_temperatures(10)        
        response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/temperature')         
        assert(response.status == 200)        
        data = json.loads(content)
        assert(len(data) == 30)
    
    def test_get_temperatures_for_timestamps(self):
        """ asks for temperatures within time bounds """
        data_for_testing.insert_dummy_temperatures(20)
        startMillis = str(int(time.time()) - 70)  # a little over a  minute ago        
        endMillis = str(int(time.time()))
        response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/temperature?start=' + startMillis + '&end=' + endMillis)        
        assert(response.status == 200)                
        data = json.loads(content)
        assert(len(data) == 6)
        
    def test_get_options(self):
        response, content = self._call_GET_with_credentials('http://localhost:8080/chestfreezer/api/options')
        assert response.status == 200
        print content
        data = json.loads(content)
        assert(len(data) == 5) #5 options        
    
    def test_set_options(self):
        new_temp_store = 60;
        new_instruction_interval = 120;
        new_temp_check = 10;
        request_body = '{ "store_temperature_interval_seconds" : ' + str(new_temp_store) + ',  "instruction_interval_seconds" : ' + str(new_instruction_interval) + ',  "monitor_temperature_interval_seconds" : ' + str(new_temp_check) + ' }'        
        response = self._call_POST_with_credentials_and_body('http://localhost:8080/chestfreezer/api/options', request_body, 'application/json')[0]
        assert(response.status == 204)  
        assert configuration.store_temperature_interval_seconds() == new_temp_store      
        assert configuration.instruction_interval_seconds() == new_instruction_interval
        assert configuration.control_temperature_interval_seconds() == new_temp_check
        
    def tearDown(self):
        print '==================== Cleared DB and ended test case ==================\n'
    
if __name__ == '__main__':
    unittest.main()