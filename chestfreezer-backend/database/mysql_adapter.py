'''
Created on Apr 3, 2014

Initializes, reads and writes to a mysql database 

@author: theoklitos
'''
import MySQLdb
import util.configuration as configuration

cursor = None

TEMPERATURE_READINGS_TABLE_NAME = 'temperature_readings'

def connect():    
    db = MySQLdb.connect(host=configuration.get_db_host(), user=configuration.get_db_user(), passwd=configuration.get_db_pwd(), db=configuration.get_db_name())                
    global cursor
    cursor = db.cursor()    
    
    # check if tables exist
    temperature_table = cursor.execute("SHOW TABLES LIKE '" + TEMPERATURE_READINGS_TABLE_NAME + "'");
    if temperature_table == 0:
        # create temperature readings
        cursor.execute("CREATE TABLE " + TEMPERATURE_READINGS_TABLE_NAME + " (probe_id INT(12), temperature_C FLOAT(6,3), temparature_F FLOAT(7,4), timestamp DATE)");
        
def get_cursor():
    """ returns the mysql cursor object. Might be null. """
    return cursor

