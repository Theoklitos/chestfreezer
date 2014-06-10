'''
Created on Apr 7, 2014

Tests for the database adapter

@author: theoklitos
'''
import sys
import os
from control.brew_logic import Beer, BeerException
sys.path.append(os.path.abspath('..'))
import unittest
from database import db_adapter
from util import data_for_testing
from hardware import temperature_probes
import time
import hardware
from hardware.temperature_probes import Probe

def overwriten_db_type():
    return 'memory'

class TestDatabaseAdapter(unittest.TestCase):    
    
    def _get_number_of_tables(self):
        """ returns all the tables in the DB - works only for the in-memory version """
        db_adapter.cursor = db_adapter.db.cursor()        
        result = len(db_adapter.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
        db_adapter.cursor.close()
        return result;
    
    def _get_all_temperatures(self):
        """ returns all the temperature readings from the DB - works only in-memory """
        db_adapter.cursor = db_adapter.db.cursor()        
        db_adapter.cursor.execute("SELECT * FROM " + db_adapter.TEMPERATURE_READINGS_TABLE_NAME)
        result = db_adapter.cursor.fetchall()                
        db_adapter.cursor.close()
        return result;
    
    @classmethod
    def setUpClass(self):        
        db_adapter.configuration.db_type = overwriten_db_type
        db_adapter.connect()        
        temperature_probes.initialize_probes()
        
    def test_get_temperature_readings(self):        
        data_for_testing.insert_dummy_temperatures(10)
        startSeconds = str(int(time.time()) - 30)  # less than one minute ago        
        endSeconds = str(int(time.time()))
        result = db_adapter.get_temperature_readings(startSeconds, endSeconds)
        assert(len(result) == 3)
        startSeconds = str(int(time.time()) - 70)  # should go over one minute
        result = db_adapter.get_temperature_readings(startSeconds, endSeconds)
        assert(len(result) == 6)        
        result = db_adapter.get_temperature_readings(0, 0)
        assert(len(result) == 0)
    
    def test_drop_tables(self):        
        assert(self._get_number_of_tables() == 4)  # we begin with 4 tables
        db_adapter.drop_tables()
        assert(self._get_number_of_tables() == 0)          
    
    def test_store_temperatures(self):        
        assert(len(self._get_all_temperatures()) == 0)
        temps = [hardware.temperature_probes.TemperatureReading("1", 27), hardware.temperature_probes.TemperatureReading("2", 53)]
        db_adapter.store_temperatures(temps)
        result = self._get_all_temperatures()
        assert(len(result) == 2)
        result1 = result[0]
        assert((result1[0] == '1') & (result1[1] == 27))
        result2 = result[1]
        assert((result2[0] == '2') & (result2[1] == 53))
            
    def test_add_probe(self):
        probe = Probe("666AAA", "Dummy10")
        db_adapter.store_probe(probe)
        all_probes = db_adapter.get_all_probes()
        assert(len(all_probes) == 4)
        assert(all_probes[3].probe_id == '666AAA')
        assert(all_probes[3].name == 'Dummy10')
        
    def test_get_sizes(self):
        if overwriten_db_type() != 'memory': # only works for mysql
            size =  db_adapter.get_database_size();        
            total = size + db_adapter.get_database_free_size()
            print 'Database size: ' + str(size) + 'MB / ' + str(total) + 'MB' 
            assert size < total
    
    def test_delete_all_temperatures(self): 
        assert len(self._get_all_temperatures()) == 0
        temps = [hardware.temperature_probes.TemperatureReading("1", 27), hardware.temperature_probes.TemperatureReading("2", 53)]
        db_adapter.store_temperatures(temps)        
        assert len(self._get_all_temperatures()) == 2
        db_adapter.delete_all_temperatures()
        assert len(self._get_all_temperatures()) == 0
        
    def test_store_retrieve_beer(self):
        new_beer = Beer('Random Encounter', 'Hefeweizen', time.time() - 20000, time.time() - 10000, time.time() - 10000, time.time() - 5000, 7, 'Awesome hefe!');
        assert len(db_adapter.get_all_beers()) == 0
        db_adapter.store_beer(new_beer)
        assert len(db_adapter.get_all_beers()) == 1
        try:
            assert len(db_adapter.get_beer_by_name('wrong_name'))
            assert False                 
        except BeerException:
            pass #all good, beer did not exist (as expected)                
        retrieved_beer = db_adapter.get_beer_by_name('Random Encounter')
        assert retrieved_beer.name == new_beer.name
        # also modify some data
        retrieved_beer.name = 'Random Encounter Mk2'
        retrieved_beer.comments = 'Improved version!'
        retrieved_beer.rating = 10
        retrieved_beer._verifyDataMakeSense();
        db_adapter.store_beer(retrieved_beer)
        twice_retriever = db_adapter.get_beer_by_name('Random Encounter Mk2')
        assert twice_retriever.rating == 10
        db_adapter.delete_beer_by_name('Random Encounter Mk2')
        assert len(db_adapter.get_all_beers()) == 0
        
    def tearDown(self):        
        db_adapter.drop_tables()
        db_adapter.initialize_tables()

if __name__ == '__main__':
    unittest.main()
        
