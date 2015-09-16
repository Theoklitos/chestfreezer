'''
Created on Apr 3, 2014

Controls the temperature based on readings and user instructions. Sort of like the main logic class.

@author: theoklitos
'''
import database.db_adapter 
from hardware import chestfreezer_gpio
from util import configuration, misc_utils, emailer
from threading import Thread
import hardware, datetime, time

instruction_target_temperature_C = None
temperature_override_C = None

freezer_override = False
heater_override = False

def _should_reverse_device_state():
    ''' checks the config, if the normal relay state is OPEN then all the device states should be reversed '''
    value = configuration.normal_relay_state()
    if value == 'open': return True
    elif value == 'false': return False
    else: raise Exception('Relay normal state is neither "open" nor "closed", instead is "' + str(value) + '". Pin will not trigger.')

freezer_state = _should_reverse_device_state()
print 'Initial freezer state is: ' + str(freezer_state)
heater_state = _should_reverse_device_state()
print 'Initial heater state is: ' + str(heater_state)

instruction_thread_in_waiting = True
current_instruction_id = None

should_threads_run = True

SECONDS_IN_ONE_YEAR = 31557600 

class Instruction():
    """ an instruction that dictates what the temperature(C) should be, and in which time period it should be so """
    def __init__(self, instruction_id, instruction_target_temperature_C, from_timestamp, to_timestamp, description='No description given'):
        self.instruction_id = str(instruction_id)
        self.target_temperature_C = instruction_target_temperature_C
        self.from_timestamp = int(from_timestamp)
        self.to_timestamp = int(to_timestamp)
        if from_timestamp > to_timestamp: raise InstructionException('Start date cannot be after end date')
        self.description = description        
        
    def __str__(self):        
        return 'Instruction #' + self.instruction_id + ', description: "' + self.description + '", from ' + misc_utils.timestamp_to_datetime(self.from_timestamp).strftime("%c") + ' to ' + misc_utils.timestamp_to_datetime(self.to_timestamp).strftime("%c") + '. Target temperature: ' + str(self.target_temperature_C) + 'C'
    
    def set_from_timestamp_safe(self, value):
        """ if the 'from_timestamp' value is None or somehow malformed, will not set it """
        try:
            if value is not None:
                self.from_timestamp = int(value)
        except:
            # do nothing, value will not have changed
            pass
    
    def set_to_timestamp_safe(self, value):
        """ if the 'to_timestamp' value is None or somehow malformed, will not set it """
        try:
            if value is not None:
                self.to_timestamp = int(value)
        except:
            # do nothing, value will not have changed
            pass

class Beer():
    """ guess what this class represents! """
    def __init__(self, name, style, fermenting_from_timestamp, fermenting_to_timestamp, conditioning_from_timestamp, conditioning_to_timestamp, rating = 0, comments = 'No comments', beer_id = 0, dryhopping_from_timestamp = -1, dryhopping_to_timestamp = -1):
        self.beer_id = beer_id;
        self.name = name;
        self.style = style;
        self.fermenting_from_timestamp = int(fermenting_from_timestamp);
        self.fermenting_to_timestamp  = int(fermenting_to_timestamp);
        self.dryhopping_from_timestamp = int(dryhopping_from_timestamp);
        self.dryhopping_to_timestamp = int(dryhopping_to_timestamp);        
        self.conditioning_from_timestamp = int(conditioning_from_timestamp);
        self.conditioning_to_timestamp  = int(conditioning_to_timestamp);        
        self.rating = rating;
        self.comments = comments;        
        self._verifyDataMakeSense();
    def __str__(self):
        dryhopping_text = "";
        if (self.dryhopping_from_timestamp != -1) & (self.dryhopping_to_timestamp != -1):
            dryhopping_text = '\nDry hopping from ' + str(misc_utils.get_storeable_date_timestamp(self.dryhopping_from_timestamp)) + ' to ' + str(misc_utils.get_storeable_date_timestamp(self.dryhopping_to_timestamp))                              
        return 'Beer "' + self.name + '", style: ' + self.style + ', rating: ' + str(self.rating) + '/10. Comments: ' + self.comments + '\nFermenting period: ' + str(misc_utils.get_storeable_date_timestamp(self.fermenting_from_timestamp)) + ' to ' + str(misc_utils.get_storeable_date_timestamp(self.fermenting_to_timestamp)) + '\nConditioning period: ' + str(misc_utils.get_storeable_date_timestamp(self.conditioning_from_timestamp)) + ' to ' + str(misc_utils.get_storeable_date_timestamp(self.conditioning_to_timestamp)) + dryhopping_text
    def _verifyDataMakeSense(self):
        """ makes sure that fermenting is before conditioning, and those intervals don't overlap. Also makes sure that rating is [0,10]. Throws BeerException """
        if (self.fermenting_from_timestamp > self.fermenting_to_timestamp) | (self.conditioning_from_timestamp > self.conditioning_to_timestamp) | (self.dryhopping_from_timestamp > self.dryhopping_to_timestamp):            
            raise BeerException('A "start" date is after its matching "end" date')
        if (self.fermenting_to_timestamp > self.conditioning_from_timestamp) & (self.conditioning_from_timestamp > SECONDS_IN_ONE_YEAR):
            raise BeerException('Fermentation date is after the conditioning date')        
        if (self.fermenting_to_timestamp > self.dryhopping_from_timestamp) & (self.dryhopping_from_timestamp > SECONDS_IN_ONE_YEAR):
            raise BeerException('Fermentation date is after the dry-hopping date')        
        if (self.dryhopping_to_timestamp > self.conditioning_from_timestamp) & (self.conditioning_from_timestamp > SECONDS_IN_ONE_YEAR):
            raise BeerException('Dry-hopping date is after the conditioning date')
        if hasattr(self, 'rating'):
            if (self.rating < 0) | (self.rating > 10):
                raise BeerException('Rating must be between 0 and 10')

def start_instruction_thread():
    """ starts the thread that determines which instruction to follow and when """    
    def follow_instructions():
        global has_escalated
        has_escalated = False     
        while True:      
            global instruction_thread_in_waiting
            instruction_thread_in_waiting = False
            try:
                instructions = database.db_adapter.get_all_instructions()                
                if len(instructions) > 1:
                    pretty_date = misc_utils.get_storeable_datetime_timestamp(time.time())
                    instructions_string = ',\n'.join(map(str, instructions))
                    message = "More than one instruction for time " + pretty_date + ":\n" + instructions_string                    
                    if not has_escalated:                        
                        emailer.escalate("Instruction error", message)
                        global has_escalated
                        has_escalated = True    
                    print message                
                elif len(instructions) == 1:
                    global current_instruction_id
                    instruction = instructions[0]
                    if (current_instruction_id != instruction.instruction_id):
                        current_instruction_id = instruction.instruction_id
                        global instruction_target_temperature_C                        
                        instruction_target_temperature_C = instruction.target_temperature_C
                        print 'Applying instruction #' + instruction.instruction_id + ', setting target temperature to: ' + str(instruction_target_temperature_C) + "C"
                elif len(instructions) == 0:
                    global current_instruction_id
                    current_instruction_id = None
            except Exception as e:
                print 'Error while looking at instructions:\n' + str(e)
            instruction_thread_in_waiting = True
            time.sleep(configuration.instruction_interval_seconds())                    
    instruction_thread = Thread(target=follow_instructions, args=())
    instruction_thread.daemon = True
    instruction_thread.start()

def set_temperature_overwrite(temperature_C):
    """ will set the temperature to the given degree (C), overwriting any other instructions """
    global temperature_override_C
    temperature_override_C = float(temperature_C)

def remove_temperature_override():
    """ will clear whatever temperature override is there """
    global temperature_override_C
    temperature_override_C = None
    
class InstructionException(Exception):
    """ when an instruction should not be created in the system """
    pass

class BeerException(Exception):
    """ when something goes wrong with a beer object, usually a nonsensical date error"""
    pass

def store_instruction_for_unique_time(instruction):
    """ stores the instruction only if no other instruction is assigned to its given timeslot. """    
    results = database.db_adapter.get_instructions(instruction.from_timestamp, instruction.to_timestamp)
    if len(results) == 0: database.db_adapter._store_instruction(instruction)    
    elif (not ((len(results) == 1) & (results[0].instruction_id == instruction.instruction_id))) | (len(results) > 1):
        raise InstructionException('Instruction overlaps with one or more existing instructions')
    else: database.db_adapter._store_instruction(instruction)    
    
def _set_heater(should_activate):
    """ sets the heater state to on/off directly """        
    global heater_state
    if should_activate is not heater_state:
        heater_state = should_activate
        if _should_reverse_device_state(): should_activate = not should_activate
        chestfreezer_gpio.output_pin(configuration.heater_pin(), not should_activate) 

def _set_freezer(should_activate):
    """ sets the freezer state to on/off directly """
    global freezer_state
    if should_activate is not freezer_state:        
        freezer_state = should_activate
        if _should_reverse_device_state(): should_activate = not should_activate 
        chestfreezer_gpio.output_pin(configuration.freezer_pin(), not should_activate) 

def _is_device_overriden():
    """ returns true if there a heater or a freezer override """
    return heater_override | freezer_override  

def remove_heater_override():
    """ removes any override to the heater state """
    global heater_override 
    heater_override = False

def remove_freezer_override():
    """ removes any override to the freezer state """
    global freezer_override
    freezer_override = False
    
def set_heater_override(should_activate):
    """ turns the heater on or off regardless of instructions """
    global heater_override 
    heater_override = True
    _set_heater(should_activate)    
    
def set_freezer_override(should_activate):
    """ turns the freezer on or off regardless of instructions """
    global freezer_override
    freezer_override = True
    _set_freezer(should_activate)

class StopControlThread(Exception):
    """ when the control temperature thread must immediately iterate """
    pass

def get_actual_target_temperature_C():
    """ returns the current target temperature, regardless if it has been set by an override or a instruction """
    if temperature_override_C is not None: return temperature_override_C
    else: return instruction_target_temperature_C

def start_temperature_control_thread():
    """ start the thread that monitors and control the devices in order to control the temperature """
    def control_temperature():
        while True:                   
            try:
                actual_target_C = get_actual_target_temperature_C()                
                current_temperature_C = hardware.temperature_probes.get_current_temperature()
                if _is_device_overriden() | (current_temperature_C is None) | (actual_target_C is None): raise StopControlThread  # skip iteration
                # the great and (not so) efficient algorithm!
                if misc_utils.is_within_distance(current_temperature_C, actual_target_C, configuration.temperature_tolerance()):                     
                    _set_heater(False); _set_freezer(False)                
                elif current_temperature_C < actual_target_C:
                    _set_heater(True); _set_freezer(False)
                elif current_temperature_C > actual_target_C:
                    _set_heater(False); _set_freezer(True)
            except StopControlThread as e:
                # nothing, let loop re-iterate
                pass
            except Exception as e:
                print 'Error while setting temperature:\n' + str(e)            
            time.sleep(configuration.control_temperature_interval_seconds())                    
    control_temperature_thread = Thread(target=control_temperature, args=())
    control_temperature_thread.daemon = True
    control_temperature_thread.start()

def _get_current_datetime():                    
    """ returns the current datetime """
    return datetime.datetime.now()

def _get_current_hour():
    """ returns the hour of the day in a 24h format """
    return _get_current_datetime().hour

def _get_seconds_in_hour():
    """ self-explanatory """
    seconds_in_hour = 3600;
    return seconds_in_hour

def _get_seconds_in_day():
    """ self-explanatory """
    seconds_in_day = 86400;
    return seconds_in_day
 
def _is_time_in_today(time_to_check):
    """ checks if the given timestamp is inside today """    
    today_timestamps = misc_utils.get_start_and_end_of_day(_get_current_datetime())
    #print 'TODAY is time ' + str(time_to_check) + ' between ' + str(today_timestamps[0]) + ' and ' + str(today_timestamps[1])
    return (time_to_check >= today_timestamps[0]) & (time_to_check < today_timestamps[1])

def _is_time_in_tomorrow(time_to_check):
    """ checks if the given timestamp is inside the day after today """ 
    tomorrow_timestamps = misc_utils.get_start_and_end_of_day(_get_current_datetime() + datetime.timedelta(0,misc_utils.SECONDS_IN_DAY)) 
    return (time_to_check >= tomorrow_timestamps[0]) & (time_to_check < tomorrow_timestamps[1])

def _do_beer_state_email_checks(beer, timestamp, email_function):
    """ checks the given timestamp if its within today or tomorrow, and calls the email function if so """    
    if _is_time_in_today(timestamp):
        email_function(beer, False);
    elif _is_time_in_tomorrow(timestamp):
        email_function(beer, True);

def start_beer_monitoring_thread():
    """ starts the thread that sends out email when the beer state changes """
    def monitor_beers():
        global should_threads_run
        while should_threads_run:
            if (_get_current_hour() == '0') | (_get_current_hour() == 0): # we check the beginning of every day
                print 'Its time to check whether beer emails are to be sent out!'
                for beer in database.db_adapter.get_all_beers():
                    # fermentation
                    _do_beer_state_email_checks(beer,beer.fermenting_from_timestamp, emailer.send_fermentation_email)
                    # dry-hopping
                    _do_beer_state_email_checks(beer,beer.dryhopping_from_timestamp, emailer.send_dryhopping_email)
                    # conditioning    
                    _do_beer_state_email_checks(beer,beer.conditioning_from_timestamp, emailer.send_conditioning_email)
                # all done. now sleep until the next day
                print 'Checks done. Sleeping for one day...'
                time.sleep(_get_seconds_in_day())
            else:
                # print 'Beer check wrong hour (' + str(_get_current_hour()) + '), waiting one more...'
                # not the correct hour, sleep                    
                time.sleep(_get_seconds_in_hour())
    global monitor_beers_thread
    monitor_beers_thread = Thread(target=monitor_beers, args=())    
    monitor_beers_thread.daemon = True
    monitor_beers_thread.start()

