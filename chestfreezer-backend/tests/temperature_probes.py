'''
Created on Apr 8, 2014

Tests for the temperature probe module

@author: theoklitos
'''

import unittest
from database import db_adapter
from hardware import temperature_probes

def overwriten_db_type():
    return 'memory'

class TestTemperatureProbes(unittest.TestCase):    
        
    def _get_all_temperatures(self):
        """ returns all the temperature readings from the DB - works only in-memory """
        return db_adapter.cursor.execute("SELECT * FROM " + db_adapter.TEMPERATURE_READINGS_TABLE_NAME).fetchall()
    
    @classmethod
    def setUpClass(self):        
        db_adapter.configuration.db_type = overwriten_db_type
        db_adapter.connect()        
        temperature_probes.initialize_probes()
                
    def test_set_master_probe(self):        
        temperature_probes.determine_master_probe()
        all_probes = db_adapter.get_all_probes()                
        assert(all_probes[0].master)
        assert(not all_probes[1].master)
        assert(not all_probes[2].master)
        temperature_probes.master_probe_id = all_probes[0].probe_id
        # change the master probe
        temperature_probes.set_probe_as_master(all_probes[2].probe_id)
        all_probes = db_adapter.get_all_probes()
        assert(not all_probes[0].master)
        assert(not all_probes[1].master)
        assert(all_probes[2].master)
        temperature_probes.master_probe_id = all_probes[2].probe_id
        # set no probe to master
        temperature_probes.set_probe_as_not_master(all_probes[2].probe_id)
        all_probes = db_adapter.get_all_probes()
        assert(not all_probes[0].master)
        assert(not all_probes[1].master)
        assert(not all_probes[2].master)
        
    def test_change_probe_name(self):     
        temperature_probes.set_probe_name(db_adapter.get_all_probes()[1].probe_id, "new name")
        assert(db_adapter.get_all_probes()[1].name == 'new name')        

    def tearDown(self):        
        db_adapter.drop_tables()
        db_adapter.initialize_tables()
