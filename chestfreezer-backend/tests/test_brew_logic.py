'''
Created on Apr 9, 2014

Tests for the brewing logic, instructions, and temperature settings

@author: theoklitos
'''
import unittest
from control import brew_logic
from database import db_adapter
from control.brew_logic import Instruction, InstructionException
import time
from hardware import temperature_probes

def overwriten_db_type():
    return 'memory'

class TestBrewLogic(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        brew_logic.configuration.db_type = overwriten_db_type                
        db_adapter.connect()
        
    def setUp(self):
        db_adapter.drop_tables(False)
        db_adapter.initialize_tables()
        
    def test_apply_instruction(self):
        temperature_probes._last_master_reading = 24.565
        brew_logic.configuration.set_instruction_interval_seconds(0.1)
        brew_logic.configuration.set_control_temperature_interval_seconds(0.5)                
        brew_logic.start_instruction_thread()
        brew_logic.start_temperature_control_thread()        
        instruction = Instruction(1, 10, time.time(), time.time() + 600, 'Test Instruction')        
        brew_logic.store_instruction_for_unique_time(instruction)
        time.sleep(1)
        assert(brew_logic.freezer_state)
        assert(not brew_logic.heater_state)
        temperature_probes._last_master_reading = 9.4  # now devices should stop
        time.sleep(1)        
        assert(not brew_logic.freezer_state)
        assert(brew_logic.heater_state)
        temperature_probes._last_master_reading = 10.5  # now devices should stop
        time.sleep(1)
        assert(not brew_logic.freezer_state)
        assert(not brew_logic.heater_state)
        
    def test_add_modify_delete_instruction(self):
        instruction = Instruction(None, 10, time.time() - 600, time.time(), 'Test Instruction')        
        brew_logic.store_instruction_for_unique_time(instruction)        
        instructions = db_adapter.get_all_instructions()
        assert(len(instructions) == 1)        
        new_description = 'New Description, Bla Bla Bla'
        old_instruction = db_adapter.get_all_instructions()[0]
        old_instruction.description = new_description        
        brew_logic.store_instruction_for_unique_time(old_instruction)
        instructions = db_adapter.get_all_instructions()        
        assert(len(instructions) == 1)
        assert(instructions[0].description == new_description)
        db_adapter.delete_instruction(old_instruction.instruction_id)
        assert(len(db_adapter.get_all_instructions()) == 0)
    
    def test_instructions_for_times(self):
        instruction1 = Instruction(1, 10, time.time() - 599, time.time() - 100, 'Test instruction low')
        instruction2 = Instruction(2, 30, time.time() - 1200, time.time() - 600, 'Test instruction high')
        brew_logic.store_instruction_for_unique_time(instruction1)        
        brew_logic.store_instruction_for_unique_time(instruction2)        
        assert(len(db_adapter.get_all_instructions()) == 2)        
        assert(len(db_adapter.get_instructions()) == 0)        
        results = db_adapter.get_instructions(time.time() - 300, time.time() - 300)        
        assert(instruction1.target_temperature_C == results[0].target_temperature_C)        
        results = db_adapter.get_instructions(time.time() - 1300, time.time() - 650)        
        assert(instruction2.target_temperature_C == results[0].target_temperature_C)        
        results = db_adapter.get_instructions(time.time() - 700, time.time() - 200)
        assert(len(results) == 2)
             
    def test_add_instruction_overlap(self):
        instruction1 = Instruction(1, 10, time.time() - 600, time.time(), 'overlap instruction 1')
        instruction2 = Instruction(2, 30, time.time() - 1200, time.time() - 400, 'overlap instruction 2')
        brew_logic.store_instruction_for_unique_time(instruction1)
        try:        
            brew_logic.store_instruction_for_unique_time(instruction2)
            assert(False)
        except InstructionException:
            # all good, test succeed
            pass

if __name__ == '__main__':
    unittest.main()