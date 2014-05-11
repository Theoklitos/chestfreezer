/**
 * returns encoded basic auth credentials
 */
function getBasicAuthCredentials(username, password) {
	var token = username + ':' + password;
	var hash = Base64.encode(token);
	return "Basic " + hash;
}

/**
 * will prevent the keypress event if the input is anything other than a number or a dot(.) 
 */
function allowEventOnlyOnFloats(event) {
    if(event.which < 46 || event.which > 59) {
    	event.preventDefault();
    } // prevent if not number/dot
    if(event.which == 46 && $(this).val().indexOf('.') != -1) {
    	event.preventDefault();
    } // prevent if already dot
};

/**
 * self-explanatory
 */
function capitaliseFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * returns the given timestamp as a pretty readable string
 */
function getUnixTimestampAsPrettyDate(timestamp) {
	if(timestamp == undefined) {
		return "";
	} else {
		return moment(new Date(timestamp * 1000)).format('DD/MM/YYYY h:mm A');
	}
}

/**
 * returns the current unix timestamp (in seconds)
 */
function getCurrentUnixTimestamp() {
	return Math.round(+new Date() / 1000);
}

/**
 * displays the error message in the appropriate part of the website
 */
function handleError(errorMessage) {
	console.log('Error: ' + errorMessage)
	$("#error-message-container").addClass("alert alert-danger"); 
	$("#error-message").text(errorMessage);	
}

/**
 * executes the logic after a call to the backend has been made
 */
function makeAjaxCallToBackend(method, url, properties, async, onSuccess, onError, data) {
	$.ajax({
		type : method,
		url : url,
		async : async,
		data : data,
		dataType : 'json',
		beforeSend : function(xhr) {
			xhr.setRequestHeader("Authorization", getBasicAuthCredentials(
					properties.username, properties.password));
		},
		success : function(response) {
			onSuccess(response);
		},
		error : function(xhr, status, error) {
			handleError(error);
			if(onError != undefined) {
				onError(xhr, status, error)
			}			
		}
	});
}

/**
 * sets the live temperature on the dial
 */
function setCurrentTemperature(temperatureCelcius) {
	gauge = $('#temperature-gauge').dxCircularGauge('instance');
	gauge.value(temperatureCelcius);
	$('#temperature-number').html(
			'Current Temperature: ' + temperatureCelcius + ' &degC')
}

/**
 * sets the target temperature on the subvalue on the dial
 */
function setTargetTemperature(temperatureCelcius) {
	gauge = $('#temperature-gauge').dxCircularGauge('instance');
	gauge.subvalues = [ temperatureCelcius ];
}

/**
 * checks if the given temperature came from the master probe and is thus the
 * "master" reading
 */
function isMasterTemperature(temperatureReading, data) {
	var masterProbeId;
	for ( var n in data.probes) {
		probe = data.probes[n];
		if (probe.master == "True") {
			masterProbeId = probe.probe_id;
			break;
		}
	}
	if (masterProbeId == undefined) {
		return false;
	}
	return temperatureReading.probe_id == masterProbeId;
}

/**
 * matches a probe_id to a probe_name
 */
function getProbeNameForProbeId(probeId, data) {
	for ( var n in data.probes) {
		probe = data.probes[n];
		if (probe.probe_id == probeId) {
			return probe.name;
		}
	}
}

/**
 * pushes the given temperature reading into the corrent datapoint (based on the
 * probe name
 */
function pushTempReadingIntoDatapoints(tempReading, data) {	
	for (n in data.chartData) {		
		dataForProbe = data.chartData[n];
		if(dataForProbe.name.indexOf(getProbeNameForProbeId(tempReading.probe_id, data)) > -1) {					
			dataForProbe.dataPoints.push({
				x : tempReading.timestamp * 1000,
				y : parseFloat(tempReading.temperature_C)
			});
		}
	}
}

/**
 * asks what the target temperature is and sets it on the gauge
 */
function fetchTargetTemperature(properties) {
	makeAjaxCallToBackend('GET', properties.rootUrl + '/temperature/target', properties, true,
			function(response) {
				console.log(response);
				if(response != undefined) {
					
				}				
			});
}


/**
 * gets the current applied instruction (if any), and also gets the current target
 * temperature, and displays it.
 */
function fetchCurrentInstructionAndTargetTemperature(properties, data) {
	fetchTargetTemperature(properties);
}


/**
 * calls the chestfreezer service and requests the temperatures from the time
 * periods
 */
function fetchTemperaturesForTime(fromMillis, toMillis, properties, data) {
	start = fromMillis;
	end = toMillis;
	targetUrl = properties.rootUrl + '/temperature?start=' + start + '&end=' + end;
	makeAjaxCallToBackend('GET', targetUrl, properties, true,
			function(response) {
				for ( var n in response) {
					tempReading = response[n];
					pushTempReadingIntoDatapoints(tempReading, data);
					if (isMasterTemperature(tempReading, data)) {
						setCurrentTemperature(tempReading.temperature_C);
					}
					data.chart.render();
				}
			});
}

/**
 * initializes the temperature probes
 */
function initializeProbes(properties, data) {
	makeAjaxCallToBackend('GET', properties.rootUrl + '/probe', properties,
			false, function(response) {
				for ( var n in response) {
					probe = response[n];
					data.probes.push(probe);
				}
				console.log('Initialized ' + data.probes.length + ' probes.');
			});
}

/**
 * sets the text and the selector value based on the device's json
 */
function displayDevice(deviceName, data) {
	device = data.devices[deviceName];
	capitalizedName = capitaliseFirstLetter(deviceName);
	var text = capitalizedName + ' Status: N/A';
	var selectorValue = 'AUTO';
	if(device.state == 'off') {
		text = capitalizedName + ' Status: Off';
		selectorValue = 'OFF'
	} else {
		text = capitalizedName + ' Status: On';
		selectorValue = 'ON'
	}	
	if(device.overridden == "false") {
		selectorValue = 'AUTO'
	}
	$('#' + deviceName + '-status').children('.status-text').html(text);
	$('#' + deviceName + '-selector').val(selectorValue);	
}

/**
 * reads and sets the values of the freezer and the heater
 */
function setDevices(properties, data) {
	makeAjaxCallToBackend('GET', properties.rootUrl + '/device', properties,
			false, function(response) {
				data.devices = response;
				displayDevice('freezer', data)
				displayDevice('heater', data)				
				console.log('Set ' + data.devices.length
						+ ' devices state.');
			});
}

/**
 * Initializes the graph for the temperatures for the given time interval
 */
function initializeTemperatures(secondsBeforeNow, properties, data) {
	fetchTemperaturesForTime(getCurrentUnixTimestamp() - secondsBeforeNow,
			getCurrentUnixTimestamp(), properties, data);
}

/**
 * Queries the service about the temperature and updates the graph
 */
function startTemperatureFetchingThread(temperatureUpdateIntervalSeconds, instructionUpdateIntervalSeconds, properties, data) {
	setInterval(function() {
		from = getCurrentUnixTimestamp() - temperatureUpdateIntervalSeconds;
		to = getCurrentUnixTimestamp();
		fetchTemperaturesForTime(from, to, properties, data);		
	}, temperatureUpdateIntervalSeconds * 1000);
	setInterval(function() {
		fetchCurrentInstructionAndTargetTemperature(properties, data);
	}, instructionUpdateIntervalSeconds * 1000);
}

/**
 * convert the temperature object to a data array that the chart can read
 */
function initializeChartAndData(data) {	
	for ( var n in data.probes) {
		probe = data.probes[n];		
		if(probe.master == "True") {
			probeName = probe.name + "(master)";
		} else {		
			probeName = probe.name;
		}
		data.chartData.push({
			type : "line",
			xValueType : "dateTime",
			showInLegend : true,
			name : probeName,
			dataPoints : []
		});
	};
	var chart = new CanvasJS.Chart("temperature-chart", {
		zoomEnabled : true,
		title : {
			text : "Temperature Readings"
		},
		toolTip : {
			shared : true
		},
		axisY : {
			suffix : ' ℃',
			includeZero : false
		},
		data : data.chartData
	});
	data.chart = chart; // add a reference to the chart
	chart.render();
}

/**
 * initialize the temp gauge using the chartjs library
 */
function initializeGauge() {
	$("#temperature-gauge").dxCircularGauge({
		scale : {
			majorTick : {
				color : 'black',
				tickInterval : 10
			},
			minorTick : {
				visible : true,
				color : 'black',
				tickInterval : 1
			},
			startValue : -20,
			endValue : 80
		},
		// value: 24,
		subvalues : [],
		subvalueIndicator : {
			color : 'green'
		},
		rangeContainer : {
			offset : 5,
			ranges : [ {
				startValue : -20,
				endValue : 0,
				color : 'blue'
			}, {
				startValue : 0,
				endValue : 80,
				color : 'red'
			} ]
		}
	});
}

/**
 * tries out the given credentials to the server and starts the main() function if they are valid
 */
function signin(properties) {	
	$('#login-button').button('loading');
	properties.username = $('#username').val();
	properties.password = $('#password').val();
	// make a dummy call to the probe service, if its succesful then log in, otherwise error	
	makeAjaxCallToBackend('GET', properties.rootUrl + '/probe', properties,
			true, function(response) {				
				bootbox.alert('Welcome to the Chestfreezer, ' + properties.username + '.');				
				main(properties);
			}, function(xhr, status, error) {
				$('#login-button').button('reset');
				var message = 'Error ' + xhr.status + ': ' + xhr.statusText;
				if(xhr.status == 401) {
					message += '. Your IP is logged and an administrator has been notified.'
				}
				bootbox.alert(message);				
			});	
}

/**
* sets a menu button as selected and displays its content tab (hiding the other content tabs)
*/
function menuButtonAction(menuButton, menuPanel) {
	$(menuButton).click(function() {
		$('.chestfreezer-menu-button').removeClass('active');
		$(menuButton).toggleClass('active');
		$('.chestfreezer-content').hide();
		$(menuPanel).show();
	});
}

/**
 * looks through the model data and returns the instruction with the given ID
 */
function getInstructionForId(id, data) {
	for(var n in data.instructions) {
		if(data.instructions[n].instruction_id == id) {
			return data.instructions[n];
		}
	}
	return {};
}

/**
 * sets the fields in the instruction form from the given object
 */
function setInstructionForm(instruction) {	
	$('#targetTemperature').val(instruction.target_temperature_C);
	$('#description').val(instruction.description);
	datetimeFrom = getUnixTimestampAsPrettyDate(instruction.from_timestamp);
	$('#datetime-from-value').val(datetimeFrom);
	datetimeTo = getUnixTimestampAsPrettyDate(instruction.to_timestamp);
	$('#datetime-to-value').val(datetimeTo);	
}

/**
 * fires a POST to create a new instruction
 */
function createNewInstruction(properties, formData) {
	makeAjaxCallToBackend('POST', properties.rootUrl + '/instruction', properties,
			true, function(response) {
		bootbox.alert('Instruction saved.');
		// update the view
		setInstructionForm({});
		$('#instruction-button').click();
	}, function(xhr, status, error) {
		bootbox.alert('Could not save instruction: ' + xhr.responseText + ".");
	}, formData);
}

/**
 * fires a PUT to update an instruction
 */
function updateInstruction(properties, formData, id) {	
	makeAjaxCallToBackend('PUT', properties.rootUrl + '/instruction/' + id, properties,
			true, function(response) {
		bootbox.alert('Instruction updated.');
		// update the view		
		$('#instruction-button').click();
	}, function(xhr, status, error) {
		bootbox.alert('Could not update instruction: ' + xhr.responseText + ".");
	}, formData);
}

/**
 * sets the actions on the right hand device/temperature panel
 */
function setStatusPanelActions(properties, data) {
	$('#taget-temperature-textfield').keypress(allowEventOnlyOnFloats(event));
	$("#taget-temperature-checkbox").change(function() {
		if(this.checked) {
			
		} else {
			// disable target temperautre
		}
	});
	$("#taget-temperature-button").click(function() {
		var value = $("#taget-temperature-textfield").val();
		if(value) {
			makeAjaxCallToBackend('POST', properties.rootUrl + '/temperature/target', properties,
					true, function(response) {
				bootbox.alert('Instruction saved.');
				// update the view
				setInstructionForm({});
				$('#instruction-button').click();
			}, function(xhr, status, error) {
				bootbox.alert('Could not save instruction: ' + xhr.responseText + ".");
			}, formData);			
		}
	});
}



/**
 * sets the actions and calls for the instructions menu functionality
 */
function setInstructionMenuActions(properties, data) {
	$('#targetTemperature').keypress(allowEventOnlyOnFloats(event));	
	$('#instructions-table').on('click', 'tbody tr', function(event) {
	    $(this).toggleClass('table-highlight').siblings().removeClass('table-highlight');
	    if($(this).attr('class').indexOf('table-highlight') > -1) { // if its selected
	    	var idCell = $(this)[0].firstChild;	    	
	    	data.selected_instruction_id = $(idCell).html();
	    	setInstructionForm(getInstructionForId(data.selected_instruction_id, data));
	    	$('#save-instruction').html('Update');	    	
	    } else {
	    	data.selected_instruction_id = undefined;
	    	setInstructionForm({});
	    	$('#save-instruction').html('Create');	    	
	    }
	});
	$('#instruction-button').click(function() {
		$("#instructions-table > tbody").html("");
		makeAjaxCallToBackend('GET', properties.rootUrl + '/instruction', properties,
				false, function(response) {
					for ( var n in response) {
						instruction = response[n];
						data.instructions.push(instruction)
						fromDatetime = getUnixTimestampAsPrettyDate(instruction.from_timestamp);
						toDatetime = getUnixTimestampAsPrettyDate(instruction.to_timestamp);
						$('#instructions-table-body').append('<tr><td>' + instruction.instruction_id + '</td><td>' + instruction.target_temperature_C + ' &degC</td><td>' + instruction.description + '</td><td>' + fromDatetime + '</td><td>' + toDatetime + '</td></tr>');						
					}
				console.log('Retrieved ' + response.length + ' instruction(s).');
		});		
	});
	$('#save-instruction').click(function() {
		targetTemperature = $('#targetTemperature').val();
		description = $('#description').val();
		datetimeFrom = $('#datetime-from-value').val();
		datetimeTo = $('#datetime-to-value').val();
		if(!targetTemperature || !datetimeFrom || !datetimeTo) {
			bootbox.alert('Missing instruction value(s)!');
			return;
		}
		fromTimestamp = new Date(datetimeFrom).getTime() / 1000;
		toTimestamp = new Date(datetimeTo).getTime() / 1000;		
		formData = 'target_temperature_C=' + targetTemperature + '&description=' + description + '&from_timestamp=' + fromTimestamp + '&to_timestamp=' + toTimestamp;
		if(data.selected_instruction_id == undefined) {
			createNewInstruction(properties, formData);
		} else {
			updateInstruction(properties, formData, data.selected_instruction_id);			
		}
	});
	$('#delete-instruction').click(function() {
		if(data.selected_instruction_id == undefined) {return;}		
		console.log(properties.rootUrl + '/instruction/' + data.selected_instruction_id);
		makeAjaxCallToBackend('DELETE', properties.rootUrl + '/instruction/' + data.selected_instruction_id, properties,
				true, function(response) {
			bootbox.alert('Instruction deleted.');
			// update the view		
			setInstructionForm({});
			$('#instruction-button').click();
		}, function(xhr, status, error) {			
			bootbox.alert('Could not delete instruction: ' + xhr.responseText + ".");
		}, formData);
	});
}

/**
 * sets the actions and calls for when the user clicks on the menu
 */
function setMenuClickActions(properties, data) {
	menuButtonAction($('#instruction-button'),$('#instruction-panel'));
	menuButtonAction($('#probe-button'),$('#probe-panel'));
	menuButtonAction($('#log-button'),$('#log-panel'));
	$('#datetime-from').datetimepicker();
	$('#datetime-to').datetimepicker();
	// instructions
	setInstructionMenuActions(properties, data);
	// probes
	
	// log
}

/**
 * something like a "main" function for our app
 */
function main(properties) {
	var data = {
			devices : [],
			probes : [],
			instructions : [],
			chartData : []
	};
	$('#login-page').hide();
	$('.username').html('User: ' + properties.username);	
	$('#main-page').show();
	// initialize values
	initializeProbes(properties, data);	
	setDevices(properties, data);	
	setStatusPanelActions(properties, data);
	setMenuClickActions(properties, data);
	var oneWeekSeconds = (60 * 60 * 24 * 7)
	// initializeTemperatures(oneWeekSeconds, properties, data);
	// draw stuff
	initializeGauge();
	initializeChartAndData(data);
	// begin "threads"
	startTemperatureFetchingThread(properties.temperatureUpdateIntervalSeconds, 
			properties.instructionUpdateIntervalSeconds, properties, data);
}

$(document).ready(function() {
	$.getScript("/scripts/lib/Base64.js", function() {		
		console.log('Loaded Base64.js');
		var properties = {
				rootUrl : 'http://localhost:8080/chestfreezer/api',
				temperatureUpdateIntervalSeconds : 60,
				instructionUpdateIntervalSeconds : 3,
				username : 'test-username',
				password : 'test-password'
			};
		// set the login event
		//$('#login-button').click(function() {signin(properties); return false;});
		main(properties); // enable this to skip signin
	});
});
