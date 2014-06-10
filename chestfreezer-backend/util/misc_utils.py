'''
Created on Apr 2, 2014

Various miscellaneous utils 

@author: theoklitos
'''
import os
import sys    
import termios
import fcntl
import datetime

def get_single_char():
    """ waits for user input and immediately reads the first char without waiting for a newline. 
    Found at: http://love-python.blogspot.de/2010/03/getch-in-python-get-single-character.html"""      
    fd = sys.stdin.fileno()   
    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
    
    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
    
    try:
        while 1:
            try:
                c = sys.stdin.read(1)
                break
            except IOError: pass
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
        return c
    
def timestamp_to_datetime(timestamp):
    """ converts a unix timestamp to a datetime object """
    return datetime.datetime.fromtimestamp(timestamp)

def get_storeable_datetime_timestamp(timestamp):
    """ from a unix timestsamp, returns a formatable datetime that can be stored in SQL """
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def get_storeable_date_timestamp(timestamp):
    """ from a unix timestsamp, returns a formatable date (no time!) that can be stored in SQL """
    return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d')

def is_within_distance(number, target_number, distance):
    """ returns true if the number is within 'distance' from the 'target_number' """
    actual_distance = abs(target_number - number)
    return actual_distance <= distance     

def celsius_to_fahrenheit(temperature_C):
    """ converts C -> F """
    return temperature_C * 9.0 / 5.0 + 32.0

def fahrenheit_to_celsius(temperature_F):
    """ converts F -> C """
    return (temperature_F - 32) * (5.0 / 9.0)

def append_to_file(filename, message):
    """ appends the given files to a file """
    filestream = open(filename, 'a')
    filestream.write(message + '\n')
    filestream.close() 
    
def boolean_to_readable_string(boolean_value):
    """ for a 1 returns 'False' and for a 0 returns 'True' """
    result = 'False'
    if boolean_value:
        result = 'True'
    return result
