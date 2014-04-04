'''
Created on Apr 3, 2014

Initializes, reads and writes to a mysql database. Functions as an unofficial DAO for everything.

@author: theoklitos
'''
import MySQLdb
import util.configuration as configuration
import datetime
import hardware.temperature

cursor = None
db = None

TEMPERATURE_READINGS_TABLE_NAME = 'temperature_readings'
PROBES_TABLE_NAME = 'probes'
INSTRUCTIONS_TABLE_NAME = 'instructions'

def connect():
    global db
    db = MySQLdb.connect(host=configuration.get_db_host(), user=configuration.get_db_user(), passwd=configuration.get_db_pwd(), db=configuration.get_db_name())
    global cursor
    cursor = db.cursor()

    # check if tables exist, init the database
    probe_tables = cursor.execute("SHOW TABLES LIKE '" + PROBES_TABLE_NAME + "'");
    if probe_tables == 0:
        cursor.execute("CREATE TABLE " + PROBES_TABLE_NAME + " (probe_id INT(12), probe_name VARCHAR(100), master BOOLEAN, PRIMARY KEY(probe_id))");
        
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
    global cursor
    global db
    cursor.execute("SELECT * FROM " + PROBES_TABLE_NAME + " WHERE probe_id='" + probe.probe_id + "'")
    results = cursor.fetchall()
    if len(results) == 0:
        cursor.execute("INSERT INTO " + PROBES_TABLE_NAME + " VALUES ('" + probe.probe_id + "','" + probe.name + "')")
        print 'Registered new probe #' + probe.probe_id
    elif len(results) == 1:
        if should_overwrite:
            cursor.execute("INSERT INTO " + PROBES_TABLE_NAME + " VALUES ('" + probe.probe_id + "','" + probe.name + "')")
            print 'Updated probe #' + probe.probe_id
        else:
            print 'Probe #' + probe.probe_id + ' is already registered.'
            return
    db.commit()  

def store_temperatures(temperature_readings):
    """ stores the given list of temperature readings """
    global cursor
    global db
    if cursor is not None and db is not None:
        for temperature_reading in temperature_readings:
            probe_id = temperature_reading.probe_id
            temperature_C = temperature_reading.temperature_C
            timestamp = datetime.datetime.fromtimestamp(temperature_reading.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            sql_statement = "INSERT INTO " + TEMPERATURE_READINGS_TABLE_NAME + " VALUES ('" + probe_id + "','" + str(temperature_C) + "','" 
            + timestamp + "')"            
            cursor.execute(sql_statement)
        db.commit()        

def get_readings(from_timestamp, to_timestamp):
    """ returns all the temperature readings from/upto the given timestamps """
    global cursor
    global db
    found_temperature_readings = []
    if cursor is not None and db is not None:    
        sql_statement = "SELECT * FROM " + TEMPERATURE_READINGS_TABLE_NAME + " WHERE timestamp BETWEEN from_unixtime(" + str(from_timestamp) 
        + ") and from_unixtime(" + str(to_timestamp) + ")"
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
    global cursor
    global db
    found_instructions = []
    sql_statement = "SELECT * FROM " + INSTRUCTIONS_TABLE_NAME + " WHERE from_unixtime(" + timestamp +") BETWEEN from and until"
    cursor.execute(sql_statement);
    all_results = cursor.fetchall()
    for result in all_results:
        print result        
    return found_instructions


