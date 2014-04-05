'''
Created on Apr 3, 2014

Initializes, reads and writes to a mysql database. Functions as an unofficial DAO for everything.

@author: theoklitos
'''
import MySQLdb
import util.configuration as configuration
import datetime
import hardware.temperature
from util import misc_utils

cursor = None
db = None

TEMPERATURE_READINGS_TABLE_NAME = 'temperature_readings'
PROBES_TABLE_NAME = 'probes'
INSTRUCTIONS_TABLE_NAME = 'instructions'

def connect():
    global db
    db = MySQLdb.connect(host=configuration.db_host(), user=configuration.db_user(), passwd=configuration.db_pwd(), db=configuration.db_name())
    global cursor
    cursor = db.cursor()

    # check if tables exist, init the database
    probe_tables = cursor.execute("SHOW TABLES LIKE '" + PROBES_TABLE_NAME + "'");
    if probe_tables == 0:
        cursor.execute("CREATE TABLE " + PROBES_TABLE_NAME + " (probe_id INT(12), name VARCHAR(100), master BOOLEAN, PRIMARY KEY(probe_id))");
        
    temperature_tables = cursor.execute("SHOW TABLES LIKE '" + TEMPERATURE_READINGS_TABLE_NAME + "'");
    if temperature_tables == 0:
        sql_statement = "CREATE TABLE " + TEMPERATURE_READINGS_TABLE_NAME + " (probe_id INT(12) REFERENCES " + PROBES_TABLE_NAME + "(probe_id), temperature_C FLOAT(6,3), timestamp DATETIME)"        
        cursor.execute(sql_statement);
    
    instruction_tables = cursor.execute("SHOW TABLES LIKE '" + INSTRUCTIONS_TABLE_NAME + "'");
    if instruction_tables == 0:
        # create temperature readings
        sql_statement = "CREATE TABLE " + INSTRUCTIONS_TABLE_NAME + " ( temperature_C FLOAT(6,3), start DATETIME, end DATETIME, description TEXT )"        
        cursor.execute(sql_statement);
        
def store_probe(probe, should_overwrite=True):
    """ stores (with the option to overwrite) a new probe """    
    probe_id_pruned = str(probe.probe_id)
    cursor.execute("SELECT * FROM " + PROBES_TABLE_NAME + " WHERE probe_id='" + probe_id_pruned + "'")
    results = cursor.fetchall()
    sql_statement = "INSERT INTO " + PROBES_TABLE_NAME + " VALUES ('" + probe_id_pruned + "','" + probe.name + "', FALSE)"
    if len(results) == 0:
        cursor.execute(sql_statement)
        print 'Registered new probe #' + probe_id_pruned
    elif len(results) == 1:
        if should_overwrite:
            update_sql = "UPDATE " + PROBES_TABLE_NAME + " SET name='" + probe.name + "',master='" + probe.master + "' WHERE probe_id='" + probe.probe_id + "'"
            cursor.execute(update_sql)
            print 'Updated probe #' + probe_id_pruned
        else:
            print 'Probe #' + probe_id_pruned + ' is already registered.'
            return
    db.commit()  

def store_temperatures(temperature_readings):
    """ stores the given list of temperature readings """
    if cursor is not None and db is not None:
        for temperature_reading in temperature_readings:
            probe_id = temperature_reading.probe_id
            temperature_C = temperature_reading.temperature_C
            timestamp = datetime.datetime.fromtimestamp(temperature_reading.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            sql_statement = "INSERT INTO " + TEMPERATURE_READINGS_TABLE_NAME + " VALUES ('" + probe_id + "','" + str(temperature_C) + "','" + timestamp + "')"            
            cursor.execute(sql_statement)
        db.commit()        

def get_readings(from_timestamp, to_timestamp):
    """ returns all the temperature readings from/upto the given timestamps """
    print 'Asked for readings from ' + misc_utils.timestamp_to_datetime(from_timestamp).strftime("%c") + ' to ' + misc_utils.timestamp_to_datetime(to_timestamp).strftime("%c")
    found_temperature_readings = []    
                    
    sql_statement = "SELECT * FROM " + TEMPERATURE_READINGS_TABLE_NAME + " WHERE timestamp BETWEEN from_unixtime(" + str(from_timestamp) + ") and from_unixtime(" + str(to_timestamp) + ")"
    cursor.execute(sql_statement);
    all_results = cursor.fetchall()
    for result in all_results:
        probe_id = result[0]
        temperature_C = result[1]                        
        timestamp = result[2].strftime("%s")            
        temperature_reading = hardware.temperature.TemperatureReading(probe_id, temperature_C, timestamp)
        found_temperature_readings.append(temperature_reading)                        
        
    return found_temperature_readings

def get_instructions_for_time(timestamp):
    """ reads the instructions table and returns all the instructions that would be valid for the given time """
    found_instructions = []
    sql_statement = "SELECT * FROM " + INSTRUCTIONS_TABLE_NAME + " WHERE from_unixtime(" + timestamp +") BETWEEN from and until"
    cursor.execute(sql_statement);
    all_results = cursor.fetchall()
    for result in all_results:
        print result        
    return found_instructions

def get_all_probes():
    """ returns all the probes """
    all_probes = []
    cursor.execute("SELECT * FROM " + PROBES_TABLE_NAME)
    all_results = cursor.fetchall()
    for result in all_results:
        probe_id = result[0]
        probe_name = result[1]
        master = result[2]
        probe = hardware.temperature.Probe(probe_id, probe_name, master)
        all_probes.append(probe)
    return all_probes        

def determine_master_probe():
    """ if there is no temperature probe set as the MASTER one, will set the first one """    
    first_result = None
    is_anyone_master = False
    for probe in get_all_probes():
        if first_result is None:
            first_result = probe
        if probe.master:
            is_anyone_master = True
            break    
    if not is_anyone_master:
        first_result.master = True
        store_probe(first_result)
        print 'Auto-determined probe #' + first_result.probe_id + ' to be the master one.'    
        