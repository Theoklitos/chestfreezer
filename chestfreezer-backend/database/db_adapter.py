'''
Created on Apr 3, 2014

Initializes, reads and writes to a mysql database. Functions as an unofficial DAO for everything.

@author: theoklitos
'''
import MySQLdb
import util.configuration as configuration
import datetime
import hardware.temperature_probes
import sqlite3
import sys
import time
import control.brew_logic
from util import misc_utils

cursor = None
db = None
lock_object = False

TEMPERATURE_READINGS_TABLE_NAME = 'temperature_readings'
PROBES_TABLE_NAME = 'probes'
INSTRUCTIONS_TABLE_NAME = 'instructions'
BEERS_TABLE_NAME = 'beers'
    
def synchronized(func):
    """ synchronized method decorator, from http://theorangeduck.com/page/synchronized-python """           
    #func.__lock__ = threading.Lock()            
    def cursor_and_lock_check(*args, **kws):
        global lock_object
        global cursor
        while lock_object: time.sleep(0.1)                
        lock_object = True
        cursor = db.cursor()
        try:
            returnValue = func(*args, **kws)
            return returnValue
        finally:
            cursor.close()
            lock_object = False            
    return cursor_and_lock_check

def _is_memory_db():
    """returns true if the database is only in-memory (sqlite3). Otherwise itc can be assumed that MySQL is being used """    
    if configuration.db_type() == configuration.DATABASE_IN_DISK_CONFIG_VALUE: 
        return False  
    elif configuration.db_type() == configuration.DATABASE_IN_MEMORY_CONFIG_VALUE:
        return True

def drop_tables(should_drop_probes_too=True):
    """ drops (almost) all the tables used in the app's db """
    cursor = db.cursor()    
    try:
        cursor.execute("DROP TABLE " + TEMPERATURE_READINGS_TABLE_NAME)
    except:
        pass
        # its ok, table doesnt exist at all
    if should_drop_probes_too:    
        try:
            cursor.execute("DROP TABLE " + PROBES_TABLE_NAME)
        except:
            pass
            # likewise
    try:
        cursor.execute("DROP TABLE " + INSTRUCTIONS_TABLE_NAME)
    except:
        pass
        # likewise
    try:
        cursor.execute("DROP TABLE " + BEERS_TABLE_NAME)
    except:
        pass
        # likewise
    db.commit()    

@synchronized
def does_table_exist(table_name):
    """ self-explanatory """
    if _is_memory_db():
        return len(cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='" + table_name + "'").fetchall()) == 1
    else:
        return cursor.execute("SHOW TABLES LIKE '" + table_name + "'") == 1            

def initialize_tables():
    """ initializes the 3 required tables """    
    # check if tables exist, init the database
    cursor = db.cursor()
    if not does_table_exist(PROBES_TABLE_NAME):
        cursor.execute("CREATE TABLE " + PROBES_TABLE_NAME + " (probe_id VARCHAR(12), name VARCHAR(100), master BOOLEAN, PRIMARY KEY(probe_id))");        
    if not does_table_exist(TEMPERATURE_READINGS_TABLE_NAME):    
        sql_statement = "CREATE TABLE " + TEMPERATURE_READINGS_TABLE_NAME + " (probe_id VARCHAR(12) REFERENCES " + PROBES_TABLE_NAME + "(probe_id), temperature_C FLOAT(6,3), timestamp DATETIME)"        
        cursor.execute(sql_statement);    
    if not does_table_exist(INSTRUCTIONS_TABLE_NAME):
        sql_statement = "CREATE TABLE " + INSTRUCTIONS_TABLE_NAME + " (instruction_id INT AUTO_INCREMENT, instruction_target_temperature_C FLOAT(6,3), from_timestamp DATETIME, to_timestamp DATETIME, description TEXT, PRIMARY KEY(instruction_id))"        
        cursor.execute(sql_statement);
    if not does_table_exist(BEERS_TABLE_NAME):
        sql_statement = "CREATE TABLE " + BEERS_TABLE_NAME + " (beer_id INT AUTO_INCREMENT, name VARCHAR(55) UNIQUE, style VARCHAR(55), fermenting_from DATE, fermenting_to DATE, conditioning_from DATE, conditioning_to DATE, rating INT(2), comments TEXT, PRIMARY KEY(beer_id))"        
        cursor.execute(sql_statement);

def connect():    
    global db
    global cursor    
    if _is_memory_db():
        db = sqlite3.connect(':memory:', check_same_thread=False)
        print 'Using sqlite3 in-memory database.'        
    else:            
        db = MySQLdb.connect(host=configuration.db_host(), user=configuration.db_user(), passwd=configuration.db_pwd(), db=configuration.db_name())
        print 'Using MySQL database.'
    cursor = db.cursor()
    if 'drop' in sys.argv:
        print 'Will drop all tables...',
        drop_tables()
        print 'done.'
    initialize_tables()
    cursor.close()

@synchronized
def _store_instruction(instruction):
    """ stores or updates the given instruction. This is not safe! Do not call this directly, unless you know what you are doing. 
    Use the brew_logic method that safely stores instructions  """
    from_timestamp = misc_utils.get_storeable_datetime_timestamp(instruction.from_timestamp)    
    to_timestamp = misc_utils.get_storeable_datetime_timestamp(instruction.to_timestamp)
    cursor.execute("SELECT * FROM " + INSTRUCTIONS_TABLE_NAME + " WHERE instruction_id='" + instruction.instruction_id + "'")
    results = cursor.fetchall()    
    if len(results) == 0:
        if _is_memory_db():
            insert_sql = "INSERT INTO " + INSTRUCTIONS_TABLE_NAME + " VALUES ('" + str(instruction.instruction_id) + "','" + str(instruction.target_temperature_C) + "','" + from_timestamp + "','" + to_timestamp + "','" + instruction.description + "')"
        else:
            insert_sql = "INSERT INTO " + INSTRUCTIONS_TABLE_NAME + " (instruction_target_temperature_C,from_timestamp,to_timestamp,description) VALUES ('" + str(instruction.target_temperature_C) + "','" + from_timestamp + "','" + to_timestamp + "','" + instruction.description + "')"
        cursor.execute(insert_sql)        
    elif len(results) == 1:        
        update_sql = "UPDATE " + INSTRUCTIONS_TABLE_NAME + " SET instruction_target_temperature_C='" + str(instruction.target_temperature_C) + "',from_timestamp='" + from_timestamp + "',to_timestamp='" + to_timestamp + "',description='" + instruction.description + "'"
        cursor.execute(update_sql)
    db.commit()    

@synchronized
def store_probe(probe, should_overwrite=True):            
    """ stores (with the option to overwrite) a new probe """    
    cursor.execute("SELECT * FROM " + PROBES_TABLE_NAME + " WHERE probe_id='" + probe.probe_id + "'")
    results = cursor.fetchall()    
    if len(results) == 0:        
        insert_sql = "INSERT INTO " + PROBES_TABLE_NAME + " VALUES ('" + probe.probe_id + "','" + probe.name + "', 1)"
        cursor.execute(insert_sql)
        print 'Registered new probe #' + probe.probe_id
    elif len(results) == 1:
        if should_overwrite:
            update_sql = "UPDATE " + PROBES_TABLE_NAME + " SET name='" + probe.name + "',master='" + str(int(not probe.master)) + "' WHERE probe_id='" + probe.probe_id + "'"            
            cursor.execute(update_sql)
            # print 'Updated probe #' + probe.probe_id
        else:
            print 'Probe #' + probe.probe_id + ' is already registered.'
            return
    db.commit()  
    
@synchronized
def store_temperatures(temperature_readings):
    """ stores the given list of temperature readings """
    for temperature_reading in temperature_readings:
        probe_id = temperature_reading.probe_id
        temperature_C = temperature_reading.temperature_C        
        timestamp = misc_utils.get_storeable_datetime_timestamp(temperature_reading.timestamp)
        sql_statement = "INSERT INTO " + TEMPERATURE_READINGS_TABLE_NAME + " VALUES ('" + probe_id + "','" + str(temperature_C) + "','" + timestamp + "')"            
        cursor.execute(sql_statement)
    db.commit()    

def _convert_timstamp_to_datime(timestamp, datetime_format):
    """ will call strptime with the given time format """
    try:             
        timestamp = timestamp.strftime("%s")
    except:    
        timestamp = int(datetime.datetime.strptime(timestamp, datetime_format).strftime("%s"))
    return timestamp

def _get_datetime(possible_timestamp):
    """ casts a timestamp to a datetime """
    return _convert_timstamp_to_datime(possible_timestamp,"%Y-%m-%d %H:%M:%S")  

def _get_date(possible_timestamp):
    """ casts a timestamp to a date """
    return _convert_timstamp_to_datime(possible_timestamp,"%Y-%m-%d")
    
def get_all_instruction_ids():
    """ self-explanatory """
    result = []
    for instruction in get_all_instructions():
        result.append(instruction.instruction_id)
    return result

@synchronized
def get_temperature_readings(from_timestamp=1, to_timestamp=time.time()):
    """ returns all the temperature readings from/upto the given timestamps """        
    found_temperature_readings = []
    sql_statement = None
    if _is_memory_db():                
        # i can't seem to compare dates in sqlite3 directly        
        sql_statement = "SELECT * FROM " + TEMPERATURE_READINGS_TABLE_NAME
    else:
        sql_statement = "SELECT * FROM " + TEMPERATURE_READINGS_TABLE_NAME + " WHERE timestamp BETWEEN from_unixtime(" + str(from_timestamp) + ") and from_unixtime(" + str(to_timestamp) + ")"    
    cursor.execute(sql_statement);
    all_results = cursor.fetchall()        
    for result in all_results:         
        probe_id = result[0]
        temperature_C = result[1]                
        timestamp = _get_datetime(result[2])        
        temperature_reading = hardware.temperature_probes.TemperatureReading(probe_id, temperature_C, timestamp)
        # dates must be compared "manually" if we are using sqlite3        
        should_add = (not _is_memory_db()) | (_is_memory_db() & (timestamp >= int(from_timestamp)) & (timestamp <= int(to_timestamp)))
        if should_add:
            found_temperature_readings.append(temperature_reading)                
    return found_temperature_readings

def _cursor_row_to_instruction(row):
    """ gets the list from the given cursor row and creates an instruction object from it """    
    instruction_id = row[0]
    instruction_target_temperature_C = row[1]    
    start_timestamp = _get_datetime(row[2])
    end_timestamp = _get_datetime(row[3])
    description = row[4]
    instruction = control.brew_logic.Instruction(instruction_id, instruction_target_temperature_C, start_timestamp, end_timestamp, description)
    return instruction

def _is_time_between(timestamp, from_timestamp, to_timestamp):
    """ self-explanatory """
    return (timestamp > from_timestamp) & (timestamp < to_timestamp)

@synchronized
def get_instructions(from_timestamp=time.time(), to_timestamp=time.time()): #max unix time
    """ reads the instructions table and returns all the instructions that would be valid for the given time """
    found_instructions = []
    sql_statement = "SELECT * FROM " + INSTRUCTIONS_TABLE_NAME    
    cursor.execute(sql_statement);
    all_results = cursor.fetchall()
    for result in all_results:
        instruction = _cursor_row_to_instruction(result)
        one_way_abut = _is_time_between(instruction.from_timestamp, from_timestamp, to_timestamp) | _is_time_between(instruction.to_timestamp, from_timestamp, to_timestamp) 
        other_way_abut = _is_time_between(from_timestamp, instruction.from_timestamp, instruction.to_timestamp) | _is_time_between(to_timestamp, instruction.from_timestamp, instruction.to_timestamp)
        if one_way_abut | other_way_abut:
            found_instructions.append(instruction)                
    return found_instructions

def get_probe_by_id(probe_id):
    """ returns the given Probe instance for the id, if any """
    for probe in get_all_probes():
        if probe.probe_id == probe_id:
            return probe
        
@synchronized
def store_beer(beer):
    """ stores (or overwrites) a beer """    
    fermenting_from = str(misc_utils.get_storeable_date_timestamp(beer.fermenting_from_timestamp))
    fermenting_to = str(misc_utils.get_storeable_date_timestamp(beer.fermenting_to_timestamp))
    conditioning_from = str(misc_utils.get_storeable_date_timestamp(beer.conditioning_from_timestamp))
    conditioning_to = str(misc_utils.get_storeable_date_timestamp(beer.conditioning_to_timestamp))  
    # does the beer already exist?
    cursor.execute("SELECT * FROM " + BEERS_TABLE_NAME + " WHERE beer_id='" + str(beer.beer_id) + "'")    
    results = cursor.fetchall()    
    if len(results) != 0: # update    
        update_sql = "UPDATE " + BEERS_TABLE_NAME + " SET name='" + beer.name + "',style='" + beer.style + "',fermenting_from='" + fermenting_from + "',fermenting_to='" + fermenting_to + "',conditioning_from='" + conditioning_from + "',conditioning_to='" + conditioning_to + "',rating='" + str(beer.rating) + "',comments='" + beer.comments + "' WHERE beer_id='" + str(beer.beer_id) + "'"   
        cursor.execute(update_sql)
        print 'Updated beer #' + str(beer.beer_id) + ' named "' + beer.name + '"'
    else: # create        
        if _is_memory_db():            
            insert_sql = "INSERT INTO " + BEERS_TABLE_NAME + " (beer_id,name,style,fermenting_from,fermenting_to,conditioning_from,conditioning_to,rating,comments) VALUES (" + str(beer.beer_id) + ",'" + beer.name + "','" + beer.style + "','" + fermenting_from + "','" + fermenting_to + "','" + conditioning_from + "','" + conditioning_to + "'," + str(beer.rating) + ",'" + beer.comments + "')"       
        else:
            insert_sql = "INSERT INTO " + BEERS_TABLE_NAME + " (name,style,fermenting_from,fermenting_to,conditioning_from,conditioning_to,rating,comments) VALUES ('" + beer.name + "','" + beer.style + "','" + fermenting_from + "','" + fermenting_to + "','" + conditioning_from + "','" + conditioning_to + "'," + str(beer.rating) + ",'" + beer.comments + "')"         
        cursor.execute(insert_sql)
        print 'Created beer "' + beer.name + '"'
    db.commit()
          
def _cursor_row_to_beer(row):
    """ casts a cursor row into a Beer object """
    name = row[1]
    style = row[2]
    fermenation_from = _get_date(row[3])
    fermentation_to = _get_date(row[4])
    conditioning_from = _get_date(row[5]);
    conditioning_to = _get_date(row[6])    
    rating = int(row[7])
    comments = row[8]
    beer_id = int(row[0])
    beer = control.brew_logic.Beer(name, style, fermenation_from, fermentation_to, conditioning_from, conditioning_to, rating, comments, beer_id)    
    return beer

def _get_beer_by_name_unsynchronized(beer_name):
    """ non-synchronized version, use inside functions that already sync """
    cursor.execute("SELECT * FROM " + BEERS_TABLE_NAME + " WHERE name='" + beer_name + "'")    
    results = cursor.fetchall()    
    if len(results) == 0:        
        raise control.brew_logic.BeerException('No beer named "' + beer_name + '" found')        
    elif len(results) > 1:
        raise Exception('More than one beers named "' + beer_name + '" found! Look into the DB asap.')
    else:
        return _cursor_row_to_beer(results[0])    

@synchronized
def get_beer_by_name(beer_name):
    """ self-explanatory. Throws BeerException if 0 beers are found """
    return _get_beer_by_name_unsynchronized(beer_name)

@synchronized
def delete_beer_by_name(beer_name):
    _get_beer_by_name_unsynchronized(beer_name)
    cursor.execute("DELETE FROM " + BEERS_TABLE_NAME + " WHERE name='" + beer_name + "'")
    print 'Deleted beer "' + beer_name + '"'
    db.commit();

@synchronized
def get_beer_by_id(beer_id):
    """ returns the beer with the given id. Throws BeerException if no such beer exists """
    cursor.execute("SELECT * FROM " + BEERS_TABLE_NAME + " WHERE beer_id='" + beer_id + "'")    
    results = cursor.fetchall()    
    if len(results) == 0:        
        raise control.brew_logic.BeerException('No beer with id ' + beer_id + '" found')
    else:
        return _cursor_row_to_beer(results[0])
    
@synchronized
def get_all_beers():
    """ returns all the beers """
    all_beers = []
    cursor.execute("SELECT * FROM " + BEERS_TABLE_NAME)
    all_results = cursor.fetchall()
    for result in all_results:
        all_beers.append(_cursor_row_to_beer(result))
    return all_beers
        
@synchronized
def get_all_probes():
    """ returns all the probes """
    all_probes = []
    cursor.execute("SELECT * FROM " + PROBES_TABLE_NAME)
    all_results = cursor.fetchall()
    for result in all_results:
        probe_id = result[0]
        probe_name = result[1]                
        master = result[2] == 0        
        probe = hardware.temperature_probes.Probe(probe_id, probe_name, master)
        all_probes.append(probe)
    return all_probes      

@synchronized
def get_instruction_by_id(instruction_id):
    for instruction in _get_all_instructions_unsynchronized():
        if instruction.instruction_id == instruction_id: return instruction

def _get_all_instructions_unsynchronized():
    """ returns all the instructions, without cursor sync """
    all_instructions = []        
    cursor.execute("SELECT * FROM " + INSTRUCTIONS_TABLE_NAME)    
    all_results = cursor.fetchall()    
    for result in all_results:
        instruction = _cursor_row_to_instruction(result)
        all_instructions.append(instruction)
    return all_instructions
        
@synchronized        
def get_all_instructions():
    """ returns all the instructions, """
    return _get_all_instructions_unsynchronized()

@synchronized
def delete_instruction(instruction_id):
    """ deletes the instruction that has the given instruction ID """
    delete_sql = "DELETE FROM " + INSTRUCTIONS_TABLE_NAME + " WHERE instruction_id='%s'" % instruction_id.strip()           
    cursor.execute(delete_sql)
    db.commit()

@synchronized
def delete_all_temperatures():
    if _is_memory_db():
        cursor.execute('DELETE FROM ' + TEMPERATURE_READINGS_TABLE_NAME)
    else:
        cursor.execute('TRUNCATE TABLE ' + TEMPERATURE_READINGS_TABLE_NAME)
    
@synchronized
def get_database_size():
    if _is_memory_db():
        return -1
    else:
        cursor.execute('SELECT table_schema, sum(data_length + index_length) / 1024 / 1024 "Megabytes" FROM information_schema.TABLES WHERE table_schema="chestfreezer";')
        result = (float(cursor.fetchall()[0][1]))        
        return result

@synchronized
def get_database_free_size():
    if _is_memory_db():
        return -1
    else:
        cursor.execute('SELECT table_schema, sum( data_length + index_length ) / 1024 / 1024 "Megabytes", sum( data_free )/ 1024 / 1024 "Free Megabytes" FROM information_schema.TABLES WHERE table_schema="chestfreezer";')    
        result = (float(cursor.fetchall()[0][2]))
        return result


