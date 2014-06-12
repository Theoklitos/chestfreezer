/*
 * Makes the ajax calls to the backend  
 */
define([ 'jquery', 'utils', 'configuration', 'model', 'overlay' ], function($, utils, configuration, model, overlay) {
	return {
		
		/*
		 * wrapper around jQuerys ajax, simply executes methods after a call to the backend has been made
		 */
		makeAjaxCallToBackend : function(method, url, async, onSuccess, onError, formData, noOverlayFlag) {	
			if(utils.shouldShowOverlayForUrl(url) && noOverlayFlag == undefined) {			
				overlay.showLoadingOverlayWholeScreen(true);
			}			
			$.ajax({
				type : method,
				url : configuration.rootUrl + url,
				async : async,
				data : formData,
				dataType : 'json',
				beforeSend : function(xhr) {
					xhr.setRequestHeader("Authorization", utils.getBasicAuthCredentials(configuration.username,
							configuration.password));
				},
				success : function(response) {
					onSuccess(response);
				},
				error : function(xhr, status, error) {					
					if (onError != undefined) {
						onError(xhr, status, error)
					} else {
						responseText = "";
						if(xhr.responseText) {
							responseText = "<br>Response text: " + xhr.responseText;
						}
						statusText = "<br>Status Code: " + xhr.status;
						if(xhr.status == 0) {
							statusText = "<br>Server seems to be unreachable!"
						}
						utils.handleUncaughtError("Error while communicating with the server, for URL:<br>" + url + statusText + responseText)						
					}
				},
				complete: function() {
					if(utils.shouldShowOverlayForUrl(url) && noOverlayFlag == undefined) {
						overlay.showLoadingOverlayWholeScreen(false);
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
				overlay.alert('Device override removed.');
			}, function(xhr, status, error) {
				overlay.alert('Could not remove device override: ' + xhr.responseText + ".");
			}, formData);
		},
		
		/*
		 * toggles the overridden state of the given device
		 */
		setDeviceOverridenState : function(deviceName, state) {
			formData = 'state=' + state;
			this.makeAjaxCallToBackend('POST', '/device/' + deviceName, true, function() {
				overlay.alert(utils.capitaliseFirstLetter(deviceName) + ' succesfully overridden.');
			}, function(xhr, status, error) {
				overlay.alert('Could not set override: ' + xhr.responseText + ".");
			}, formData);
		},
		
		/*
		 * retrieves the settings from the server and applies them to this app's configuration
		 */
		getSettings : function(onSuccess, async) {
			this.makeAjaxCallToBackend('GET', '/settings', async, function(response) {				
				configuration.temperatureUpdateIntervalSeconds = response['store_temperature_interval_seconds'];				
				configuration.instructionUpdateIntervalSeconds = response['instruction_interval_seconds'];
				if(onSuccess != undefined) {
					onSuccess(response);
				}
			});
		},
		
		/*
		 * removes whatever temperature override was set, and allows instructions to dictate
		 */
		removeTemperatureOverride : function(onSuccess) {
			formData = 'override=False';
			this.makeAjaxCallToBackend('POST', '/temperature/target', true, function() {
				overlay.alert('Temperature override removed.');
				if(onSuccess != undefined) {
					onSuccess();
				}
			}, function(xhr, status, error) {
				overlay.alert('Could not remove temperature override: ' + xhr.responseText + ".");
			}, formData);
		},
		
		/*
		 * overrides the temperature setting with the given temp value
		 */
		setTemperatureOverride : function(temperatureCelsius, onSuccess) {
			formData = 'target_temperature_C=' + temperatureCelsius;
			this.makeAjaxCallToBackend('POST', '/temperature/target', true, function() {
				overlay.alert('Temperature override succesfully set.');
				if(onSuccess != undefined) {
					onSuccess();
				}
			}, function(xhr, status, error) {
				overlay.alert('Could not set temperature override: ' + xhr.responseText + ".");
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
		 * calls the backend and updates the beer list in the model
		 */
		updateBeers : function(onSuccess) {
			this.makeAjaxCallToBackend('GET', '/beer', true, function(response) {				
				model.beers = response;
				if(onSuccess != undefined) {
					onSuccess();
				}
			});
		},
		
		/*
		 * creates a new beer
		 */
		createBeer : function(onSuccess, beerName) {
			formData = "name=" + beerName;
			this.makeAjaxCallToBackend('POST', '/beer', true, function(response) {
				if(onSuccess != undefined) {
					onSuccess();
				};
			}, function(xhr, status, error) {
				overlay.alert('Could not create beer: ' + xhr.responseText);
			}, formData);
		},
		
		/*
		 * deletes a beer
		 */
		deleteBeer : function(onSuccess, beerId) {
			this.makeAjaxCallToBackend('DELETE', '/beer/' + beerId, true, function(response) {
				if(onSuccess != undefined) {
					onSuccess();
				}
			}, function(xhr, status, error) {
				overlay.alert('Could not delete beer: ' + xhr.responseText + ".");
			});
		},
		
		/*
		 * will update the beer object passed in the backend 
		 */
		modifyBeer : function(onSuccess, beer) {
			this.makeAjaxCallToBackend('PUT', '/beer/' + beer.beer_id, true, function(response) {
				if(onSuccess != undefined) {
					onSuccess();
				}
			}, function(xhr, status, error) {
				overlay.alert('Could not update beer "' + beer.name + '": ' + xhr.responseText);
			}, beer);
		},

		/*
		 * stores json information in the model about the state of the freezer and the cooler
		 */
		updateDevices : function(onSuccess) {			
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
		updateInstructions : function(onSuccess, noOverlayFlag) {			
			this.makeAjaxCallToBackend('GET', '/instruction', false, function(response) {				
				model.instructions = response;
			}, undefined, undefined, noOverlayFlag);
			this.updateActiveInstruction(onSuccess, noOverlayFlag);
		},
		
		/*
		 * deletes the given instruction by its id
		 */
		deleteInstruction : function(instructionId, onSuccess) {
			this.makeAjaxCallToBackend('DELETE', '/instruction/' + instructionId, true, function() {
				overlay.alert('Instruction #' + instructionId + ' deleted.');
				if(onSuccess != undefined) {
					onSuccess();
				}
			}, function(xhr, status, error) {
				overlay.alert('Could not delete instruction: ' + xhr.responseText + ".");
			});
		},
		
		/*
		 * stores in the model whatever instruction is currently the "active" one, if any
		 */
		updateActiveInstruction : function(onSuccess, noOverlayFlag) {
			this.makeAjaxCallToBackend('GET', '/instruction?now', true, function(response) {				
				model.active_instruction = response;
				if(onSuccess != undefined) {
					onSuccess();
				}
			}, undefined, undefined, noOverlayFlag);
		},
		
		/*
		 * calls the backend to update the data of the given probe 
		 */
		updateProbe : function(probe, onSuccess) {
			formData = 'name=' + probe.name + '&master=' + probe.master;			
			this.makeAjaxCallToBackend('PUT', '/probe/' + probe.probe_id, true, function() {
				if(onSuccess != undefined) {
					onSuccess()
				}
			}, function(xhr, status, error) {
				overlay.alert('Could not update probe: ' + xhr.responseText + ".");
			}, formData);
		},
		
		/*
		 * PUTs data to update an instruction
		 */
		updateInstruction : function(formData, instruction_id, onSuccess) {			
			this.makeAjaxCallToBackend('PUT', '/instruction/' + instruction_id, true, function() {
				overlay.alert('Instruction successfully updated.');
				if(onSucccess != undefined) {
					onSuccess();
				}
			}, function(xhr, status, error) {
				overlay.alert('Could not update instruction: ' + xhr.responseText + ".");
			}, formData);
		},
		
		/*
		 * POSTs the form data to create a new instructions
		 */
		createNewInstruction : function(formData, onSuccess) {			
			this.makeAjaxCallToBackend('POST', '/instruction', true, function() {
				overlay.alert('Instruction successfully created.');
				if(onSuccess != undefined) {
					onSuccess();
				}
			}, function(xhr, status, error) {
				overlay.alert('Could not create instruction: ' + xhr.responseText + ".");
			}, formData);
		},

		/*
		 * executes the given method after a succesful sing-in to any url in the service. If succesful, also sets the
		 * auth properties
		 */
		doAfterSignin : function(username, password, onSuccess) {
			$('#login-button').button('loading');
			configuration.username = username;
			configuration.password = password;
			// make a dummy call to the probe service, if its succesful then log in, otherwise error
			this.makeAjaxCallToBackend('GET', '/probe', true, function(response) {
				onSuccess();
			}, function(xhr, status, error) {
				$('#login-button').button('reset');
				var message = 'Error ' + xhr.status + ': ' + xhr.statusText;
				if (xhr.status == 401) {
					message += '. Your IP is logged and an administrator has been notified.'
				}
				overlay.alert(message);
			});
		}, 
		
		/*
		 * calls the chestfreezer service and requests the temperatures from the given time periods, which are then
		 * stored into the model.
		 */
		updateTemperaturesForTime : function(fromMillis, toMillis, doWithTemperatureReading, doFinally) {			
			targetUrl = '/temperature?start=' + fromMillis + '&end=' + toMillis;
			this.makeAjaxCallToBackend('GET', targetUrl, true, function(response) {
				for(var n in response) {
					tempReading = response[n];
					doWithTemperatureReading(tempReading);					
				}
				if(doFinally != undefined) {
					doFinally();
				}
			});
		},
		
		/*
		 * calls the API endpoint to wipe all the temperatures in the DB
		 */
		deleteTemperatures : function(onSuccess) {
			this.makeAjaxCallToBackend('DELETE', '/temperature', true, function(response) {
				if(onSuccess != undefined) {
					onSuccess();
				}
			});
		},
		
		/*
		 * updates the server's settings
		 */
		updateSettings: function(temperatureToleranceC, onSuccess) {
			formData = "store_temperature_interval_seconds=" + configuration.temperatureUpdateIntervalSeconds;
			formData += "&instruction_interval_seconds=" + configuration.instructionUpdateIntervalSeconds;
			if(temperatureTolerance != undefined) {
				formData += "&temperature_tolerance_C=" + temperatureToleranceC; 
			}
			this.makeAjaxCallToBackend('POST', '/settings', true, function(response) {
				if(onSuccess != undefined) {
					onSuccess();
				}
			}, function(xhr, status, error) {
				overlay.alert('Could not update options: ' + xhr.responseText + ".");
			}, formData);
		},
	}
});
