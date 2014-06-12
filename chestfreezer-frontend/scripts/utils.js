/*
 * Various helper/utility functions  
 */
define([ 'jquery', 'configuration', 'overlay', 'Base64', 'model', 'moment' ], function($, config, overlay, Base64, model, moment) {
	return {
		/*
		 * returns encoded basic auth credentials, ready to be put into the header
		 */
		getBasicAuthCredentials : function(username, password) {
			var token = username + ':' + password;
			var hash = Base64.encode(token);
			return "Basic " + hash;
		},

		/*
		 * did this temperature reading originate from the master probe?
		 */
		isMasterTemperature : function(temperatureReading) {
			var masterProbeId;
			for ( var n in model.probes) {
				probe = model.probes[n];
				if (probe.master == "True") {
					masterProbeId = probe.probe_id;
					break;
				}
			}
			if (masterProbeId == undefined) {
				return false;
			}
			return temperatureReading.probe_id == masterProbeId;
		},

		/*
		 * matches a probe_id to a probe_name in the model
		 */
		getProbeNameForProbeId : function(probeId) {
			var result = this.getProbeForId(probeId);
			if(result != undefined) {
				return result.name;
			}
		},
		
		/*
		 * matches a probe_id to a probe in the model
		 */
		getProbeForId : function(probeId) {
			for ( var n in model.probes) {
				probe = model.probes[n];
				if (probe.probe_id == probeId) {
					return probe;
				}
			}
		},

		/*
		 * will prevent the keypress event if the input is anything other than a number or a dot(.)
		 */
		allowEventOnlyOnFloats : function allowEventOnlyOnFloats(event) {
			if (event.which < 46 || event.which > 59) {
				event.preventDefault();
			} // prevent if not number/dot
			if (event.which == 46 && $(this).val().indexOf('.') != -1) {
				event.preventDefault();
			} // prevent if already dot
		},

		/*
		 * self-explanatory
		 */
		capitaliseFirstLetter : function(string) {
			return string.charAt(0).toUpperCase() + string.slice(1);
		},
		
		/*
		 * returns true if at least one probe is set to be the master
		 */
		isAnyProbeMaster : function(probeList) {
			for(var n in probeList) {
				probe = probeList[n];
				if(probe.master == 'True') {
					return true;
				}
			}
			return false;
		},
		
		/*
		 * checks if there exists another probe with the same id in the model, and if so, returns
		 * true if its internal state is different
		 */
		hasChanged : function(probe) {			
			var found = this.getProbeForId(probe.probe_id)			
			if(found == undefined) {
				return false;
			}			
			return ! (found.name == probe.name && found.master == probe.master);
		},
		
		/*
		 * also self-explanatory
		 */
		getTextBetween : function(text, from, to) {			
			var start_pos = text.indexOf(from) + 1;
			var end_pos = test_str.indexOf(to,start_pos);
			return test_str.substring(start_pos,end_pos);			
		},

		/*
		 * returns the current time as a pretty (human) readable string
		 */
		getNowPretyDateTime: function() {
			return this.getUnixTimestampAsPrettyDate(this.getCurrentUnixTimestamp());
		},
		
		/*
		 * returns the formatted date as a unix timestamp 
		 */
		getDateAsUnixTimestamp: function(date) {			
			if(date == 'Undefined') {
				return -3600;
			} else {
				return moment(date, 'DD/MM/YYYY').unix();
			}			
		},
		
		/*
		 * returns the given timestamp as a pretty (human) readable string
		 */
		getUnixTimestampAsPrettyDateTime : function(timestamp) {
			if (timestamp == undefined) {
				return "";
			} else {
				return moment(new Date(timestamp * 1000)).format('DD/MM/YYYY h:mm A');
			}
		},
		
		/*
		 * returns the given timestamp as a pretty (human) readable string - no time, only date
		 */
		getUnixTimestampAsPrettyDate : function(timestamp) {
			if (timestamp == undefined) {
				return "";
			} else {
				return moment(new Date(timestamp * 1000)).format('DD/MM/YYYY');
			}
		},

		/*
		 * returns the current unix timestamp (in seconds)
		 */
		getCurrentUnixTimestamp : function() {
			return Math.round(+new Date() / 1000);
		},
		
		/*
		 * looks through the model data and returns the instruction with the given ID
		 */
		getInstructionForId : function(id) {
			for(var n in model.instructions) {
				if(model.instructions[n].instruction_id == id) {
					return model.instructions[n];
				}
			}
			return {};
		},
		
		/*
		 * looks up the beer for the given id, and returns it 
		 */
		getBeerForId : function(id) {			
			for(var n in model.beers) {
				if(model.beers[n].beer_id == id) {					
					return model.beers[n];
				}
			}
			return {};
		},
		
		/*
		 * adds the id to the beers in the model, but only if its unique
		 */
		addSelectedBeerId : function(selectedBeerId) {			
			for(var n = 0; n < model.beer_ids_to_update.length; n++) {
				if(model.beer_ids_to_update[n] == selectedBeerId) {
					return;
				}
			}
			model.beer_ids_to_update.push(selectedBeerId)
		},
		
		/*
		 * clicks on the beer row with the given id (if it exists)
		 */
		clickOnBeerRow : function(id) {
			if($('#beer-table').length != 0) {
				$('#beer-table tr').each(function (i, row) {
					$(row).find('td').each(function (n) {
						value = $(this).html();
						if(n == 0 && (value == id)) {
							$(this).click();
							return false;
						}
					});
				});
			}
		},
	
		/*
		 * creates a json object out of the given beer id row, if any
		 */
		getBeerFromTableRow : function(id) {
			var utilsReference = this;
			var beer = undefined;
			if($('#beer-table').length != 0) {				
				$('#beer-table tr').each(function (i, row) {
					$(row).find('td').each(function (n) {
						value = $(this).html();
						if(n == 0 && (value == id)) {							
							beer = {};			
							beer['beer_id'] = id;
						} else if(n == 1 && beer !=undefined) {
							beer['name'] = value;
						} else if(n == 2 && beer !=undefined) {
							beer['style'] = value;
						} else if(n == 3 && beer !=undefined) {
							beer['fermenting_from'] = utilsReference.getDateAsUnixTimestamp(value);
						} else if(n == 4 && beer !=undefined) {
							beer['fermenting_to'] = utilsReference.getDateAsUnixTimestamp(value);
						} else if(n == 5 && beer !=undefined) {
							beer['dryhopping_from'] = utilsReference.getDateAsUnixTimestamp(value);
						} else if(n == 6 && beer !=undefined) {
							beer['dryhopping_to'] = utilsReference.getDateAsUnixTimestamp(value);
						} else if(n == 7 && beer !=undefined) {
							beer['conditioning_from'] = utilsReference.getDateAsUnixTimestamp(value);
						} else if(n == 8 && beer !=undefined) {
							beer['conditioning_to'] = utilsReference.getDateAsUnixTimestamp(value);
						} else if(n == 9 && beer !=undefined) {
							beer['rating'] = parseInt(value);
						} else if(n == 10 && beer !=undefined) {
							fullComments = $(this).find(".full-comments").html();
							beer['comments'] = fullComments;
							return false;
						} 
					});
					if(beer != undefined) {						
						return false;
					}
				});					
			}
			return beer;
		},

		/*
		 * reads the 5 fields that the user must input to create a new instruction, validates, and returns a payload for
		 * a ajax request
		 */
		evaluateInstructionFormAndGetData : function() {
			targetTemperature = $('#targetTemperature').val();
			description = $('#description').val();
			datetimeFrom = $('#datetime-from-value').val();			
			datetimeTo = $('#datetime-to-value').val();
			if (!targetTemperature || !datetimeFrom || !datetimeTo) {
				throw 'Missing instruction value(s)!';
			}
			fromTimestamp = moment(datetimeFrom, 'DD/MM/YYYY h:mm A').unix();
			toTimestamp = moment(datetimeTo, 'DD/MM/YYYY h:mm A').unix();			
			return 'target_temperature_C=' + targetTemperature + '&description=' + description + '&from_timestamp='
					+ fromTimestamp + '&to_timestamp=' + toTimestamp;
		},
		
		/*
		 * returns true if all the fields in the settings form are submitted
		 */
		checkSettingsForm : function() {
			return (!$('#temperature-interval').val() || !$('#temperature-tolerance').val() || !$('#instruction-interval').val() || !$('#chart-history').val())						
		},
		
		/*
		 * returns true if the given url is one of the urls that should show a loading overlay over the page
		 */
		shouldShowOverlayForUrl : function (url) {
			return !(url.indexOf("/temperature?start=") > -1) && !(url.indexOf("/device") > -1) && !(url.indexOf("/temperature/target") > -1);					
		},		
		
		/*
		 * what to do when there is an unspecified error?
		 */
		handleUncaughtError : function (exception) {			
			config.stopThreads = true;
			overlay.showLoadingOverlayWholeScreen(false);		
			overlay.showLoadingOverlayChart(false);
			clearInterval(this.temperatureInterval);
			overlay.alert('Unfortunately, the website crashed due to an unexpected error:<br><strong>' + exception + '</strong>', function() {				
				window.location.reload(); // refresh the page
			});			
		},
		
		/*
		 * if the text is above 15 characters, returns the 10 first + three dots at the end
		 */
		getPrunedText : function (text) {
			if(text.length > 15) {
				return text.substring(0,15) + '...';
			} else {
				return text;
			}
		}		
	}
});
