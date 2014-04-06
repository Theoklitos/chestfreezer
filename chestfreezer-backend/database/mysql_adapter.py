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


def drop_tables():
    """ drops all the tables used in the app's db """
    try:
        cursor.execute("DROP TABLE " + TEMPERATURE_READINGS_TABLE_NAME)
    except:
        pass
        # its ok, table doesnt exist at all    
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
    db.commit()

def connect():
    global db
    db = MySQLdb.connect(host=configuration.db_host(), user=configuration.db_user(), passwd=configuration.db_pwd(), db=configuration.db_name())
    global cursor
    cursor = db.cursor()

    drop_tables() #comment out when live
    
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
    cursor.execute("SELECT * FROM " + PROBES_TABLE_NAME + " WHERE probe_id='" + probe.probe_id + "'")
    results = cursor.fetchall()
    sql_statement = "INSERT INTO " + PROBES_TABLE_NAME + " VALUES ('" + probe.probe_id + "','" + probe.name + "', FALSE)"
    if len(results) == 0:
        cursor.execute(sql_statement)
        print 'Registered new probe #' + probe.probe_id
    elif len(results) == 1:
        if should_overwrite:
            update_sql = "UPDATE " + PROBES_TABLE_NAME + " SET name='" + probe.name + "',master='" + str(int(probe.master)) + "' WHERE probe_id='" + probe.probe_id + "'"
            cursor.execute(update_sql)
            print 'Updated probe #' + probe.probe_id
        else:
            print 'Probe #' + probe.probe_id + ' is already registered.'
            return
    db.commit()  

def store_temperatures(temperature_readings):
    """ stores the given list of temperature readings """    
    print 
    for temperature_reading in temperature_readings:
        probe_id = temperature_reading.probe_id
        temperature_C = temperature_reading.temperature_C
        timestamp = datetime.datetime.fromtimestamp(temperature_reading.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        print 'Storing temperature reading: ' + str(temperature_reading)
        sql_statement = "INSERT INTO " + TEMPERATURE_READINGS_TABLE_NAME + " VALUES ('" + probe_id + "','" + str(temperature_C) + "','" + timestamp + "')"            
        cursor.execute(sql_statement)
    db.commit()
    print         

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
    sql_statement = "SELECT * FROM " + INSTRUCTIONS_TABLE_NAME + " WHERE from_unixtime(" + timestamp + ") BETWEEN from and until"
    cursor.execute(sql_statement);
    all_results = cursor.fetchall()
    for result in all_results:
        print result        
    return found_instructions

def get_master_probe():
    """ returns the probe set to master """
    for probe in get_all_probes():
        if probe.master:
            return probe

def set_probe_name(probe_id, new_name):
    """ changes the probe's name """
    for probe in get_all_probes():
        if probe.probe_id == probe_id:
            probe.name = new_name
            store_probe(probe)
            return
    raise Exception('Could not find probe #' + probe_id + ', no update done.')    

def get_probe_by_id(probe_id):
    """ returns the given Probe instance for the id, if any """
    for probe in get_all_probes():
        if probe.probe_id == probe_id:
            return probe

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

   
        
