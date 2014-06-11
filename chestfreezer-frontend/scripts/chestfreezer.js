requirejs.config({
	paths : {
		// 'jquery' : 'lib/jquery-2.1.1.min',
		'jquery' : 'http://ajax.googleapis.com/ajax/libs/jquery/2.1.0/jquery.min',
		'bootstrap' : '//netdna.bootstrapcdn.com/bootstrap/3.0.0/js/bootstrap.min',
		'bootbox' : 'lib/bootbox.min',
		'globalize' : 'http://ajax.aspnetcdn.com/ajax/globalize/0.1.1/globalize.min',
		'domReady' : 'lib/domReady',
		'chartjs' : 'http://cdn3.devexpress.com/jslib/13.2.9/js/dx.chartjs',
		'canvasjs' : 'lib/canvasjs.min',
		'moment' : 'lib/moment.min',
		'bootstrap-datetimepicker' : 'lib/bootstrap-datetimepicker.min',
		'Base64' : 'lib/Base64',
		'hbs' : 'lib/hbs'
	},
	shim : {
		'domReady' : {
			deps : [ 'bootstrap' ]
		},
		'bootstrap' : {
			deps : [ 'jquery', 'moment', 'bootstrap-datetimepicker' ]
		},
		'chartjs' : {
			deps : [ 'jquery' ]
		},
		'Base64' : {
			exports : 'Base64'
		},
		'chartjs' : {
			deps : [ 'globalize' ]
		}
	},
	hbs : {
		templateExtension : 'html',
		helperPathCallback : function(name) {
			return '/templates/helpers/' + name + '.js';
		}
	}
});

/*
 * pushes the given temperature reading into the correct datapoint (based on the probe name
 */
function pushTempReadingIntoDatapoints(model, utils, tempReading) {
	for (n in model.chartData) {
		dataForProbe = model.chartData[n];
		if (dataForProbe.name.indexOf(utils.getProbeNameForProbeId(tempReading.probe_id)) > -1) {
			var timestamp = tempReading.timestamp * 1000;
			dataForProbe.dataPoints.push({
				x : timestamp,
				y : parseFloat(tempReading.temperature_C),
			});
		}
	}
}

/*
 * Polls the temperatures for the given time period, and also sets the current temperature
 */
function fetchTemperatures(api, view, model, utils, startMillis, endMillis, callback) {	
	view.overlay.showLoadingOverlayChart(true);
	api.updateTemperaturesForTime(startMillis, endMillis, function(temperatureReading) {
		pushTempReadingIntoDatapoints(model, utils, temperatureReading);
		if (utils.isMasterTemperature(temperatureReading)) {
			view.setCurrentTemperature(tempReading.temperature_C);
		}		
	}, function() { 
		// this happens after all the temperatures have been read
		view.chart.render();
		view.overlay.showLoadingOverlayChart(false);
		if(callback != undefined) {
			callback();
		}
	});
}

/*
 * starts a timer that updates from the server the instructions and target temperature 
 */
function startInstructionAndTargetTemperatureUpdateThread(api, view, model, config, log) {
	var threadFunction = function(){
	    clearInterval(interval);
	    view.updateInstructionsAndTargetTemperature();
		log.log('Updated instructions and target temperature');	    
	    interval = setInterval(threadFunction, config.getInstructionsUpdateIntervalSeconds());
	}
	var interval = setInterval(threadFunction(), config.getInstructionsUpdateIntervalSeconds());	
}

/*
 * starts a timer that polls the server about the latest temp readings
 */
function startTemperatureUpdateThread(api, view, model, utils, config, log) {	
	var threadFunction = function(){		
	    clearInterval(interval);	    
	    startMillis = utils.getCurrentUnixTimestamp() - config.temperatureUpdateIntervalSeconds;
		endMillis = utils.getCurrentUnixTimestamp();
		fetchTemperatures(api, view, model, utils, startMillis, endMillis);
		log.log('Updated temperature readings', true);	    
	    interval = setInterval(threadFunction, config.getTemperatureUpdateIntervalSeconds());
	}
	var interval = setInterval(threadFunction(), config.getTemperatureUpdateIntervalSeconds());
}

/*
 * starts a timer that polls the server about the state of the freezer & heater
 */
function startDeviceUpdateThread(api, view, model, utils, config, log) {
	var threadFunction = function(){
	    clearInterval(interval);
	    view.updateDevices();
		log.log('Updated device state');	    
	    interval = setInterval(threadFunction, config.getDeviceUpdateIntervalSeconds());
	}
	var interval = setInterval(threadFunction(), config.getDeviceUpdateIntervalSeconds());	
}

/*
 * sets the event for when the user toggles the device state in the dropdown
 */
function setDeviceDropdownEvent(api, view, log, deviceName) {
	var element = $('#' + deviceName + '-selector');
	$(document).on('change', '#' + deviceName + '-selector', function() {
		value = $(this).val();
		if (value == 'AUTO') {
			api.removeDeviceOverride(deviceName);
			log.log("Removed " + deviceName + "'s override");
		} else if (value == 'ON') {
			api.setDeviceOverridenState(deviceName, true);
			log.log('Manually turned ' + deviceName + ' on')
		} else if (value == 'OFF') {
			api.setDeviceOverridenState(deviceName, false);
			log.log('Manually turned ' + deviceName + ' off')
		}
		view.updateDevices();
	});
}

/*
 * sets the events in the right-side status panel
 */
function setStatusPanelEvents(api, view, utils, log) {
	$(document).on('keypress', '#taget-temperature-textfield', function(event) {	
		utils.allowEventOnlyOnFloats(event);
	});
	$("#taget-temperature-checkbox").change(function() {
		if (this.checked) {
			view.enableTemperatureOverridePanel(true);			
		} else {
			api.removeTemperatureOverride(function() {
				view.updateTargetTemperature();
				log.log('Removed temperature override')
			});
		}
	});
	$("#taget-temperature-button").click(function() {
		var value = $("#taget-temperature-textfield").val();
		if (value) {
			api.setTemperatureOverride(value, function() {				
				view.updateTargetTemperature();
				log.log('Set temperature override to ' + value + ' ℃')
			});
		}
	});
	// also set the dropdown events
	setDeviceDropdownEvent(api, view, log, 'freezer');
	setDeviceDropdownEvent(api, view, log, 'heater');
}

/*
 * sets the actions for the instruction panel
 */
function setInstructionEvents(api, view, model, utils, log) {	
	$('#instruction-menu-button').click(function() {
		view.setActiveMenuButton(this);
		view.showInstructions();
		view.scrollDown();
		return false;
	});
	$(document).on('keypress', '#targetTemperature', function(event) {
		utils.allowEventOnlyOnFloats(event);
	});
	// the table row select event
	$(document).on('click', '#instructions-table tbody tr', function(event) {		
		view.setRowHighlighted($(this), true);		
		if ($(this).attr('class').indexOf('table-highlight') > -1) { // if its selected
			model.selected_instruction_id = $('.table-highlight').children('.id-cell').html();
			var selectedInstruction = utils.getInstructionForId(model.selected_instruction_id);
			view.setInstructionForm(selectedInstruction);
		} else {
			model.selected_instruction_id = undefined;
			view.setInstructionForm(); // clear the form
		}
	});
	// and the two button events
	$(document).on('click', '#save-instruction', function() {		
		try {
			formData = utils.evaluateInstructionFormAndGetData();			
			if (model.selected_instruction_id == undefined) {
				api.createNewInstruction(formData, function() {
					view.showInstructions();
					log.log('New instruction created');
				});				
			} else {
				api.updateInstruction(formData, model.selected_instruction_id, function() {
					view.showInstructions();
					log.log('instruction #' + model.selected_instruction_id + ' updated');
				});				
			}
		} catch (e) {
			// some sort of validation error
			view.alert(e);
		} finally {
			return false;
		}
	});
	$(document).on('click', '#delete-instruction', function() {
		if (!(model.selected_instruction_id == undefined)) {
			api.deleteInstruction(model.selected_instruction_id, function() {
				view.updateInstructions();
				log.log('instruction #' + model.selected_instruction_id + ' deleted')
				model.selected_instruction_id = undefined;					
			});
		}
		return false;
	});
}

/*
 * sets the actions for the probe panel
 */
function setProbeEvents(api, view, model, utils, config, log) {
	$('#probe-menu-button').click(function() {
		view.setActiveMenuButton(this);		
		view.showProbes();
		return false;
	});		
	$(document).on('click', 'input.master-checkbox', function(event) {		
	    $('input.master-checkbox').removeAttr('checked');	    
	    $(event.target).prop('checked', true);
	});
	$(document).on('click', '#update-probe-button', function() {
		var atLeastOneChange = false;
		probeList = view.getProbesFromTable();
		if(!utils.isAnyProbeMaster(probeList)) {
			view.alert('Error: At least one probe must be set to master!');
			return;
		}
		for(n in probeList) {
			probeFromTable = probeList[n];
			if(utils.hasChanged(probeFromTable)) {				
				api.updateProbe(probeFromTable);
				atLeastOneChange = true;
			} 
		}
		if(atLeastOneChange) { // refresh probe view if an update has occurred
			view.showProbes(function() {
				initializeChart(api, view, model, utils, config, log)
				view.alert('Probe(s) updated succesfully');
				log.log('Updated probes')
			});			
		}
	});
}

/*
 * sets the actions for the log panel
 */
function setLogEvents(api, view, model, utils, log) {
	$(document).on('change', '#dont-show-temp-updates', function() {		
		log.dontShowTemperatureEvents = $('#dont-show-temp-updates').is(':checked');
		view.showLog();
		return false;
	});
	$('#log-menu-button').click(function() {
		view.setActiveMenuButton(this);
		view.showLog();
		return false;
	});
}

/*
 * sets the actions for the settings panel
 */
function setSettingsEvents(api, view, model, utils, config, log) {
	$('#settings-menu-button').click(function() {
		view.setActiveMenuButton(this);
		view.showSettings();
		return false;
	});
	$(document).on('keypress', '#temperature-interval', function(event) {
		utils.allowEventOnlyOnFloats(event);
	});
	$(document).on('keypress', '#temperature-tolerance', function(event) {
		utils.allowEventOnlyOnFloats(event);
	});
	$(document).on('keypress', '#instruction-interval', function(event) {
		utils.allowEventOnlyOnFloats(event);
	});
	$(document).on('keypress', '#device-interval', function(event) {
		utils.allowEventOnlyOnFloats(event);
	});
	$(document).on('keypress', '#chart-history', function(event) {
		utils.allowEventOnlyOnFloats(event);
	});	
	$(document).on('click', '#delete-temperature-readings', function() {		
		api.deleteTemperatures(function() {			
			view.alert('All temperatures deleted from the database.')
			log.log('Deleted all temperatures');
			view.showSettings();
			initializeChart(api, view, model, utils, config, log);
		});
		return false;
	});
	$(document).on('click', '#update-settings', function() {
		config.temperatureUpdateIntervalSeconds = parseInt($('#temperature-interval').val());
		temperatureTolerance = parseFloat($('#temperature-tolerance').val());
		config.instructionUpdateIntervalSeconds = parseInt($('#instruction-interval').val());
		config.devicesUpdateIntervalSeconds = parseInt($('#device-interval').val());
		var daysPastChanged = false;
		var newDaysPast = parseInt($('#chart-history').val());
		if(config.daysPastToShowInChart != newDaysPast) {
			daysPastChanged = true;
			config.daysPastToShowInChart = newDaysPast;
		}
		api.updateSettings(temperatureTolerance, function() {
			view.alert('Updated settings.')
			log.log('Updated settings');			
			view.showSettings();
			if(daysPastChanged) {
				initializeChart(api, view, model, utils, config, log)
			}
		});
		return false;
	});
}

/*
 * and the events for the beer-tracker tab 
 */
function setBeerTrackerEvents(api, view, model, utils, config, log) {
	$('#beertracker-menu-button').click(function() {
		model.beer_ids_to_update = [];
		view.setActiveMenuButton(this);
		view.showBeerTracker();
		view.scrollDown();
		return false;
	});
	$(document).on('keypress', '#beer-table tbody td', function(e) {
		//do nothing on enter
	    if (e.keyCode === 13) { 
	    	$(this).blur();
	    	return false;
	    } else if($(this).hasClass('ratings-cell')) { // ratings cell only numbers	    	
	    	if (event.which < 46 || event.which > 59) {
	    		event.preventDefault();	    		 
	    	} 
	    }
	});	
	// format the ratings cell
	$(document).on('blur', '#beer-table .ratings-cell', function(e) {
		cell = $(this);
		if(parseInt(cell.html()) < 0) {
			cell.html("0")
    	} if(parseInt(cell.html()) > 10) {
    		cell.html("10")
    	} else {
    		parsedValue = parseInt(cell.html());
    		cell.html(parsedValue)
    	}    	
	});
	// show a textarea prompt for the comments
	$(document).on('click', '#beer-table .comments-cell', function(e) {
		cell = $(this);
		view.showPrompt('Comment on this beer:', function(message) {
			if(!message) {
				message = "No comments"
			}
			cell.html(message);
    	});
	});
	// the table row select event
	$(document).on('click', '#beer-table tbody tr', function(event) {		
		view.setRowHighlighted($(this), false);
		if ($(this).attr('class').indexOf('table-highlight') > -1) { // if its selected
			model.selected_beer_id = $('.table-highlight').children('.id-cell').html();			
			var selectedBeer = utils.getBeerForId(model.selected_beer_id);
			$('#delete-beer-button').attr('value', 'Delete beer "' + selectedBeer.name + '"')
			$('#delete-beer-button').prop('disabled',false)
			utils.addSelectedBeerId(model.selected_beer_id)
		} else {
			model.selected_beer_id = undefined;
			$('#delete-beer-button').attr('value', 'Delete...')
			$('#delete-beer-button').prop('disabled',true)
		}
	});
	$(document).on('click', '#update-beers-button', function() {
		for (var n = 0; n < model.beer_ids_to_update.length; n++) {			
			beerToUpdate = utils.getBeerFromTableRow(model.beer_ids_to_update[n]);
			console.log(beerToUpdate)
			isLastBeer = (n == model.beer_ids_to_update.length-1);
			api.modifyBeer(function() {
				log.log('Beer "' + beerToUpdate.name + '" updated');				
				if(isLastBeer) {
					// last element, show message
					view.alert('Beer(s) succesfully updated.');
				}
			},beerToUpdate);
		}
	});
	$(document).on('click', '#create-beer-button', function() {
		view.showPrompt("Give a name for this beer:", function(beerName) {
			api.createBeer(function() {
				view.alert('New beer succesfully created.')
				log.log('Beer "' + beerName + '" created');
				view.showBeerTracker();
			}, beerName);
		});		
	});
	$(document).on('click', '#delete-beer-button', function() {
		if(model.selected_beer_id != undefined) {
			api.deleteBeer(function() {
				view.alert('Beer deleted.')
				log.log('Beer #' + model.selected_beer_id + ' deleted');
				view.showBeerTracker();
			}, model.selected_beer_id);
		}
	});	
}

/*
 * adds all the jquery/js events for clicks, in the whole app
 */
function setEvents(api, view, model, utils, config, log) {
	setStatusPanelEvents(api, view, utils, log);
	setInstructionEvents(api, view, model, utils, log);
	setProbeEvents(api, view, model, utils, config, log);
	setSettingsEvents(api, view, model, utils, config, log);
	setBeerTrackerEvents(api, view, model, utils, config, log);
	setLogEvents(api, view, model, utils, log);		
}

/*
 * after reading the probes, initializes the chart going back a configuration-specified number of days 
 */
function initializeChart(api, view, model, utils, config, log, callback) {
	// read probe info and initialize the chart data structure
	// the chart data structure needs to be very specific, see http://canvasjs.com/
	api.updateProbeInfo(function() {
		model.chartData = [];
		for (var n in model.probes) {
			var probe = model.probes[n];
			if (probe.master == "True") {
				probeName = probe.name + "(master)";
			} else {
				probeName = probe.name;
			}		
			model.chartData.push({
				type : "line",				
				xValueType : "dateTime",				
				showInLegend : true,				
				name : probeName,
				dataPoints : []
			});
		}		
		view.initializeChart(model.chartData);
		now = utils.getCurrentUnixTimestamp() 
		startDate = config.daysPastToShowInChart * (24 * 60 * 60) // seconds in the given days
		fetchTemperatures(api, view, model, utils, now-startDate, now, function() {
			if(callback != undefined) {
				callback();
			}
		});		
	});
}
/*
 * main method
 */
function main(utils, api, model, config, view, log) {
	try {				
		// initialize data & view
		view.overlay.showLoadingOverlayWholeScreen(true)		
		view.showMainPageForUser(config.username);
		view.updateDevices();	
		view.initializeGauge();
		view.updateTargetTemperature();
		initializeChart(api, view, model, utils, config, log, function() {
			api.getSettings(undefined, false); // async call, needs to be first
			log.log('Data initialized');
			startTemperatureUpdateThread(api, view, model, utils, config, log);
		});		
		view.overlay.showLoadingOverlayWholeScreen(false)
				
		// add click events
		setEvents(api, view, model, utils, config, log);
		log.log('Events set');
		
		// start the update threads	
		startInstructionAndTargetTemperatureUpdateThread(api, view, model, config, log);
		startDeviceUpdateThread(api, view, model, utils, config, log)		
		log.log('Main function end');		
	} catch(exception) {
		// "uncaught" exception! close all overlays and display msg
		log.log('Uncaught exception!')
		view.overlay.showLoadingOverlayWholeScreen(false)		
		view.overlay.showLoadingOverlayChart(false)
		exception.message ? view.alert(exception.message) : view.alert(exception);
		throw exception
	}
}

/*
 * wrapper with log-in functionality around the main function
 */
require([ 'domReady', 'utils', 'apiCaller', 'model', 'configuration', 'view', 'log' ], function(domReady, utils,
		api, model, config, view, log) {
	domReady(function() {
		log.log('Main function start');		
		if (config.showLoginForm) {
			view.showLoginForm(true);
			$('#login-button').click(function() {
				api.doAfterSignin($('#username').val(), $('#password').val(), function() {
					view.alert('Welcome to the Chestfreezer, ' + config.username + '.');
					view.showLoginForm(false);
					main(utils, api, model, config, view, log);
				});
				return false;
			});
		} else {
			main(utils, api, model, config, view, log);
		}
	});
});
