'''
Created on Apr 7, 2014

Tests for the database adapter

@author: theoklitos
'''
import unittest
from database import db_adapter
from tests import test_data
from hardware import temperature_probes
import time

def overwriten_db_type():
    return 'memory'

class TestChestfreezerStartup(unittest.TestCase):    
    
    def _get_number_of_tables(self):
        """ returns all the tables in the DB - works only for the in-memory version """
        return len(db_adapter.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
    
    @classmethod
    def setUpClass(self):        
        db_adapter.configuration.db_type = overwriten_db_type
        db_adapter.connect()        
        temperature_probes.initialize_probes()
        
    def test_get_temperature_readings(self):        
        test_data.insert_test_temperatures(10)
        startMillis = str(int(time.time()) - 30) #less than one minute ago        
        endMillis = str(int(time.time()))
        result = db_adapter.get_temperature_readings(startMillis, endMillis)
        assert(len(result) == 3)
    
    def test_drop_tables(self):        
        assert(self._get_number_of_tables() == 3) # we begin with 3 tables
        db_adapter.drop_tables()
        assert(self._get_number_of_tables() == 0) # we begin with 3 tables        
    
    def test_store_temperatures(self):
        assert(False)
    
    def test_set_master_probe(self):
        assert(False)
        
    def test_add_probe(self):
        assert(False)
        
    def change_probe_name(self):
        assert(False)
            
    def tearDown(self):
        # bad way of terminating the thread
        db_adapter.drop_tables()
        db_adapter.initialize_tables()
        
