/*
 * Makes the ajax calls to the backend  
 */
define([ 'jquery', 'utils', 'configuration', 'model', 'view' ], function($, utils, config, model, view) {
	return {
		/*
		 * wrapper around jQuerys ajax, simply executes methods after a call to the backend has been made
		 */
		makeAjaxCallToBackend : function(method, url, async, onSuccess, onError, formData) {
			$.ajax({
				type : method,
				url : config.rootUrl + url,
				async : async,
				data : formData,
				dataType : 'json',
				beforeSend : function(xhr) {
					xhr.setRequestHeader("Authorization", utils.getBasicAuthCredentials(config.username,
							config.password));
				},
				success : function(response) {
					onSuccess(response);
				},
				error : function(xhr, status, error) {
					view.handleError(error);
					if (onError != undefined) {
						onError(xhr, status, error)
					} 
				}
			});
		},
		
		/*
		 * removes any overridden state of the given device
		 */
		removeDeviceOverride : function(deviceName) {
			formData = 'override=False';
			this.makeAjaxCallToBackend('POST', '/device/' + deviceName, true, function() {
				view.alert('Device override removed.');
			}, function(xhr, status, error) {
				view.alert('Could not remove device override: ' + xhr.responseText + ".");
			}, formData);
		},
		
		/*
		 * toggles the overridden state of the given device
		 */
		setDeviceOverridenState : function(deviceName, state) {
			formData = 'state=' + state;
			this.makeAjaxCallToBackend('POST', '/device/' + deviceName, true, function() {
				view.alert(utils.capitaliseFirstLetter(deviceName) + ' succesfully overridden.');
			}, function(xhr, status, error) {
				view.alert('Could not set override: ' + xhr.responseText + ".");
			}, formData);
		},
		
		/*
		 * removes whatever temperature override was set, and allows instructions to dictate
		 */
		removeTemperatureOverride : function() {
			formData = 'override=False';
			this.makeAjaxCallToBackend('POST', '/temperature/target', true, function() {
				view.alert('Temperature override removed.');
			}, function(xhr, status, error) {
				view.alert('Could not remove temperature override: ' + xhr.responseText + ".");
			}, formData);
		},
		
		/*
		 * overrides the temperature setting with the given temp value
		 */
		setTemperatureOverride : function(temperatureCelsius) {
			formData = 'target_temperature_C=' + temperatureCelsius;
			this.makeAjaxCallToBackend('POST', '/temperature/target', true, function() {
				view.alert('Temperature override succesfully set.');
			}, function(xhr, status, error) {
				view.alert('Could not set temperature override: ' + xhr.responseText + ".");
			}, formData);
		},

		/*
		 * gets the current 'target' temperature - might return 'undefined' if none is set
		 */
		getTargetTemperature : function(onSuccess) {
			this.makeAjaxCallToBackend('GET', '/temperature/target', true, function(response) {
				if(response == undefined) {
					targetTemperature = '';
					isOverride = false;
				} else {
					targetTemperature = response['target_temperature_C'];
					isOverride = response['overridden'] == 'true';
				}
				onSuccess(targetTemperature, isOverride);
			});
		},
		
		/*
		 * stores json information in the model about the temperature probes
		 */
		updateProbeInfo : function(onSuccess) {
			this.makeAjaxCallToBackend('GET', '/probe', true, function(response) {				
				model.probes = response;
				if(onSuccess != undefined) {
					onSuccess();
				}
			});
		},

		/*
		 * stores json information in the model about the state of the freezer and the cooler
		 */
		updateDeviceInfo : function(onSuccess) {			
			this.makeAjaxCallToBackend('GET', '/device', true, function(response) {				
				model.devices = response;				
				if(onSuccess != undefined) {
					onSuccess();
				}
			});
		},
		
		/*
		 * stores json information in the model about the instructions
		 */
		updateInstructions : function(onSuccess) {
			reference = this;
			this.makeAjaxCallToBackend('GET', '/instruction', true, function(response) {				
				model.instructions = response;				
				reference.updateActiveInstruction(onSuccess);				
			});
		},
		
		/*
		 * deletes the given instruction by its id
		 */
		deleteInstruction : function(instructionId) {
			this.makeAjaxCallToBackend('DELETE', '/instruction/' + instructionId, true, function() {
				view.alert('Instruction #' + instructionId + ' deleted.');
			}, function(xhr, status, error) {
				view.alert('Could not delete instruction: ' + xhr.responseText + ".");
			});
		},
		
		/*
		 * stores in the model whatever instruction is currently the "active" one, if any
		 */
		updateActiveInstruction : function(onSuccess) {
			this.makeAjaxCallToBackend('GET', '/instruction?now', true, function(response) {				
				model.active_instruction = response;
				if(onSuccess != undefined) {
					onSuccess();
				}
			});
		},
		
		/*
		 * calls the backend to update the data of the given probe 
		 */
		updateProbe : function(probe) {
			formData = 'name=' + probe.name + '&master=' + probe.master;			
			this.makeAjaxCallToBackend('PUT', '/probe/' + probe.probe_id, true, function() {
				// do nothing on success, probes are updated in batches
			}, function(xhr, status, error) {
				view.alert('Could not update probe: ' + xhr.responseText + ".");
			}, formData);
		},
		
		/*
		 * PUTs data to update an instruction
		 */
		updateInstruction : function(formData, instruction_id) {
			console.log('updating with: ' + formData)
			this.makeAjaxCallToBackend('PUT', '/instruction/' + instruction_id, true, function() {
				view.alert('Instruction successfully updated.');
			}, function(xhr, status, error) {
				view.alert('Could not update instruction: ' + xhr.responseText + ".");
			}, formData);
		},
		
		/*
		 * POSTs the form data to create a new instructions
		 */
		createNewInstruction : function(formData) {			
			this.makeAjaxCallToBackend('POST', '/instruction', true, function() {
				view.alert('Instruction successfully created.');
			}, function(xhr, status, error) {
				view.alert('Could not create instruction: ' + xhr.responseText + ".");
			}, formData);
		},

		/*
		 * executes the given method after a succesful sing-in to any url in the service. If succesful, also sets the
		 * auth properties
		 */
		doAfterSignin : function(username, password, onSuccess) {
			$('#login-button').button('loading');
			config.username = username;
			config.password = password;
			// make a dummy call to the probe service, if its succesful then log in, otherwise error
			this.makeAjaxCallToBackend('GET', '/probe', true, function(response) {
				onSuccess();
			}, function(xhr, status, error) {
				$('#login-button').button('reset');
				var message = 'Error ' + xhr.status + ': ' + xhr.statusText;
				if (xhr.status == 401) {
					message += '. Your IP is logged and an administrator has been notified.'
				}
				view.alert(message);
			});
		}, 
		
		/*
		 * calls the chestfreezer service and requests the temperatures from the given time periods, which are then
		 * stored into the model.
		 */
		updateTemperaturesForTime : function(fromMillis, toMillis, doWithTemperatureReading) {			
			targetUrl = '/temperature?start=' + fromMillis + '&end=' + toMillis;
			this.makeAjaxCallToBackend('GET', targetUrl, true, function(response) {
				for(var n in response) {
					tempReading = response[n];
					doWithTemperatureReading(tempReading);					
				}
			});
		}
	}
});
