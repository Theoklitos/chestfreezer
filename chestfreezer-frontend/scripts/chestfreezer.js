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
			dataForProbe.dataPoints.push({
				x : tempReading.timestamp * 1000,
				y : parseFloat(tempReading.temperature_C)
			});
		}
	}
}

/*
 * gets the temperatures for the given time period, and also sets the current temperature
 */
function fetchTemperatures(api, model, view, utils, startMillis, endMillis) {
	api.updateTemperaturesForTime(startMillis, endMillis, function(temperatureReading) {
		pushTempReadingIntoDatapoints(model, utils, temperatureReading);
		if (utils.isMasterTemperature(temperatureReading)) {
			view.setCurrentTemperature(tempReading.temperature_C);
		}
		view.chart.render();
	});
}

/*
 * initializes the chart, and setup the temperature data array that the chart can read
 */
function initializeChart(model, view) {
	for ( var n in model.probes) {
		probe = model.probes[n];
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
	;
	view.initializeChart(model.chartData);
}

/*
 * what is called every X seconds when updating instrucions
 */
function instructionAndTargetTemperatureThredWork(api, view, model, log) {
	updateInstructions(api, view, model);
	updateTargetTemperature(api, view);
	log.log('Updated instruction and target temperature');
}

/*
 * starts a timer that updates from the server the a) instructions and b) target temperature 
 */
function startInstructionAndTargetTemperatureUpdateThread(api, view, model, config, log) {
	instructionAndTargetTemperatureThredWork(api, view, model, log)
	setInterval(function() {
		instructionAndTargetTemperatureThredWork(api, view, model, log)		
	}, config.instructionUpdateIntervalSeconds * 1000);
}

/*
 * starts a timer that polls the server about the latest temp readings
 */
function startTemperatureUpdateThread(api, view, model, utils, config, log) {	
	setInterval(function() {
		startMillis = utils.getCurrentUnixTimestamp() - config.temperatureUpdateIntervalSeconds;
		endMillis = utils.getCurrentUnixTimestamp();
		fetchTemperatures(api, model, view, utils, startMillis, endMillis);
		log.log('Updated temperature readings', true);		
	}, config.temperatureUpdateIntervalSeconds * 1000);
}

/*
 * sets the event for when the user toggles the device state
 */
function setDeviceSelectorEvent(api, view, model, log, deviceName) {
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
		updateDeviceInfo(api, view, model);
	});
}

/*
 * sets the events in the main window and the status panel
 */
function setStatusPanelEvents(api, view, model, utils, log) {
	// target temperature stuff
	$(document).on('keypress', '#taget-temperature-textfield', function(event) {	
		utils.allowEventOnlyOnFloats(event);
	});
	$("#taget-temperature-checkbox").change(function() {
		if (this.checked) {
			view.enableTemperatureOverridePanel(true);			
		} else {
			api.removeTemperatureOverride();
			updateTargetTemperature(api, view);
			log.log('Removed temperature override')
		}
	});
	$("#taget-temperature-button").click(function() {
		var value = $("#taget-temperature-textfield").val();
		if (value) {
			api.setTemperatureOverride(value);
			updateTargetTemperature(api, view);
			log.log('Set temperature override to ' + value + ' ℃')
		}
	});
	// set device events
	setDeviceSelectorEvent(api, view, model, log, 'freezer');
	setDeviceSelectorEvent(api, view, model, log, 'heater');
}

/*
 * updates the: instruction list and the current temperature 
 */
function updateAfterInstructionChanged(api, view, model) {
	updateInstructions(api, view, model);
	updateTargetTemperature(api, view);
}
/*
 * sets the actions for the instruction panel
 */
function setInstructionEvents(api, view, model, utils) {	
	$('#instruction-menu-button').click(function() {
		view.setActiveMenuButton(this);
		updateInstructions(api, view, model);
		return false;
	});
	$(document).on('keypress', '#targetTemperature', function(event) {
		utils.allowEventOnlyOnFloats(event);
	});
	// the table select event
	$(document).on('click', '#instructions-table tbody tr', function(event) {		
		view.setInstructionRowHighlighted($(this));		
		if ($(this).attr('class').indexOf('table-highlight') > -1) { // if its selected
			model.selected_instruction_id = $('.table-highlight').children('.id-cell').html();
			var selectedInstruction = utils.getInstructionForId(model.selected_instruction_id);
			view.setInstructionForm(selectedInstruction);
		} else {
			model.selected_instruction_id = undefined;
			view.setInstructionForm(); // clear the form
		}
	});
	$(document).on('click', '#save-instruction', function() {		
		try {
			formData = utils.evaluateInstructionFormAndGetData();			
			if (model.selected_instruction_id == undefined) {
				api.createNewInstruction(formData);
				log.log('New instruction created')
			} else {
				api.updateInstruction(formData, model.selected_instruction_id);
				log.log('instruction #' + model.selected_instruction_id + ' updated')
			}
			updateAfterInstructionChanged(api, view, model);
		} catch (e) {
			// evaluation exception
			view.alert(e.message);
		}
		return false;
	});
	$('#delete-instruction').on('click', function() {
		if (!data.selected_instruction_id == undefined) {
			api.deleteInstruction(data.selected_instruction_id);
			updateAfterInstructionChanged(api, view, model);
			log.log('instruction #' + model.selected_instruction_id + ' deleted')
		}
		return false;
	});
}

/*
 * sets the actions for the probe panel
 */
function setProbeEvents(api, view, model, utils, log) {
	$('#probe-menu-button').click(function() {
		view.setActiveMenuButton(this);
		api.updateProbeInfo(function() {
			view.showProbes(model.probes);
		});
		return false;
	});
}

/*
 * Calls the backend to get the instructions and updates them in the view
 */
function updateInstructions(api, view, model) {
	api.updateInstructions(function() {
		view.showInstructions(model.instructions);
		view.displayActiveInstruction(model.active_instruction);
	});
}

/*
 * sets the actions for the log panel
 */
function setLogEvents(api, view, utils, log) {
	$(document).on('change', '#dont-show-temp-updates', function() {		
		log.dontShowTemperatureEvents = this.checked;
		view.refreshLog();
	});
	$('#log-menu-button').click(function() {
		view.setActiveMenuButton(this);
		view.showLog();
		return false;
	});
}

/*
 * adds all the jquery/js events for clicks, in the whole app
 */
function setEvents(api, view, model, utils, log) {
	setStatusPanelEvents(api, view, model, utils, log);
	setInstructionEvents(api, view, model, utils, log);
	setProbeEvents(api, view, model, utils, log);
	setLogEvents(api, view, utils, log);
}

/*
 * gets the target temperature and updates the guage and the status panel
 */
function updateTargetTemperature(api, view) {
	api.getTargetTemperature(function(targetTemperature, isOverride) {
		view.setTargetTemperature(targetTemperature, isOverride);
	});
}

/*
 * calls the backend and updates the device text + select
 */
function updateDeviceInfo(api, view, model) {
	api.updateDeviceInfo(function() {
		view.updateDevices(model.devices);
	});
}

/*
 * main method
 */
function main(domReady, utils, api, model, config, view, log) {
	view.showMainPageForUser(config.username);

	// initialize data and display
	api.updateProbeInfo(function() {
		initializeChart(model, view);
	});
	updateDeviceInfo(api, view, model);
	// fetchTemperatures(api, model, view, utils, 0, utils.getCurrentUnixTimestamp());
	view.initializeGauge();

	log.log('Data initialized');
	
	// add click events
	setEvents(api, view, model, utils, log);

	// start the update threads
	startTemperatureUpdateThread(api, view, model, utils, config, log);
	startInstructionAndTargetTemperatureUpdateThread(api, view, model, config, log);
	
	log.log('Main function end');
}

/*
 * wrapper with log-in functionality around the main function
 */
require([ 'domReady', 'utils', 'apiCaller', 'model', 'configuration', 'view', 'log', 'bootstrap' ], function(domReady, utils,
		api, model, config, view, log) {
	domReady(function() {
		log.log('Main function start');
		if (config.showLoginForm) {
			view.showLoginForm(true);
			$('#login-button').click(function() {
				api.doAfterSignin($('#username').val(), $('#username').val(), function() {
					view.alert('Welcome to the Chestfreezer, ' + config.username + '.');
					view.showLoginForm(false);
					main(domReady, utils, api, model, config, view, log);
				});
				return false;
			});
		} else {
			main(domReady, utils, api, model, config, view, log);
		}
	});
});
