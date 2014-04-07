Chestfreezer
============

A small python application that is meant to be run in a raspberry-pi connected to a beer brewing system. This 
requires a raspberry with have 1 to 10 DS18B20 temperature sensor(s) and 2 relays connected to the GPIO pins.
A rough guide on how this system was built can be found [in my blog](http://beerdeveloper.wordpress.com/). 
The python script has been tested in ubuntu and debian, of course if you are not on a raspberry-pi the GPIO
and temperature sensors will be dummies (i.e. will read/write fake values).


Overview
--------
Two devices should be connected to the relays: A "heater" and a "freezer". This way our raspberry-pi becomes a 
thermostat. Temperatures are measured from the sensors, and target temperatures can be set by the user. The two
relay devices can also be controlled directly.


Temperature Algorithm
---------------------
Nothing yet. The idea is to turn on the freezer if its warm, or turn on the cooler if its hot. Of course this is
very inefficient and should be amended in the future.


API
---
There are several resources one can call directly:
* WIP
Access control is a single username/password in the config file.

Frontend
--------
There is a simple javascript frontend using HTML5 graphs and some jQuery to visualize the data and control the sensors.



Configuration
-------------
Start the script with bin/chestfreezer.py. A 'configuration' file is included with all the options. Also, there exist 
some development-handy CL parameters:
* 'skip-gpio-test', to skip the relay on/off test
* 'drop', to drop (and re-create) all the DB tables at startup
* 'insert-test-data', to insert many dummy temperature sensor readings in the database. 
