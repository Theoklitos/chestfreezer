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

The basic mechanism is the "instruction", which is a target temperature that is to be maintained along with 
two timestamps (start, end) that define the time interval in which we wish this temperature to be maintained


Temperature Algorithm
---------------------
The idea is to turn on the freezer if its warm, or turn on the cooler if its hot, with one or two degrees as a buffer.


API
---
There are several resources one can call directly, values can be given either as a form or in JSON format:

* __GET /chestfrezer/api/temperature__, in order to get all the readings so far. Query parameters _start_ and _end_
as unit timestamps can specify a range of readings.
* __GET /chestfrezer/api/temperature/target__, for information about the current target temperature that is attempted to
be maintained.
* __POST /chestfrezer/api/temperature/target__ in order to set a temperature directly (also referred to as an override).

* __GET /chestfrezer/api/instruction__, to get all the instructions. Instructions can also be time filtered by
a _start_ and _end_ timestamp query parameters. You can also use a _now_ query parameter to get the active one.
* __POST /chestfrezer/api/instruction__, to create a new instruction.
* __PUT /chestfrezer/api/instruction/{id}__, to update an existing instruction, and
* __DELETE /chestfrezer/api/instruction/{id}__, to delete it.

* __GET /chestfrezer/api/temperature/probe__, to get all the existing temperature sensors. A temp. sensor has an unique 
hardware-bound ID and a settable name, and also a "master" boolean value that determines which is the probe that defines 
the actual tempetarure.
* __PUT /chestfrezer/api/temperature/probe/{id}__, to modify an existing probe's data.

* __GET /chestfrezer/api/temperature/device__, to get the state of the freezer and the cooler.
* __POST /chestfrezer/api/temperature/device/{device_name}__ in order to switch the freezer or cooler on/off.

Access control is a single username/password in the config file that is matched to the Basic auth header.


Frontend
--------
A small javascript single page app that uses requirejs, bootstrap and handlebars and some canvasjs graphs polls the server for
temperature updates and also controls the devices.


Configuration
-------------
Start the script with bin/chestfreezer.py. A 'configuration' file is included with all the options. Also, there exist 
some development-handy CL parameters:
* 'skip-gpio-test', to skip the relay on/off test
* 'drop', to drop (and re-create) all the DB tables at startup
* 'insert-test-data', to insert many dummy temperature sensor readings in the database. 
