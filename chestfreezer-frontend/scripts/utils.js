/*
 * Various helper/utility functions  
 */
define([ 'jquery', 'Base64', 'model' ], function($, Base64, model) {
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
		 * returns the given timestamp as a pretty (human) readable string
		 */
		getUnixTimestampAsPrettyDate : function(timestamp) {
			if (timestamp == undefined) {
				return "";
			} else {
				return moment(new Date(timestamp * 1000)).format('DD/MM/YYYY h:mm A');
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
		 * reads the 5 fields that the user must input to create a new instruction, validates, and returns a payload for
		 * a ajax request
		 */
		evaluateInstructionFormAndGetData : function() {
			targetTemperature = $('#targetTemperature').val();
			description = $('#description').val();
			datetimeFrom = $('#datetime-from-value').val();
			datetimeTo = $('#datetime-to-value').val();
			if (!targetTemperature || !datetimeFrom || !datetimeTo) {
				throw new Exception('Missing instruction value(s)!');
			}
			fromTimestamp = new Date(datetimeFrom).getTime() / 1000;
			toTimestamp = new Date(datetimeTo).getTime() / 1000;
			return 'target_temperature_C=' + targetTemperature + '&description=' + description + '&from_timestamp='
					+ fromTimestamp + '&to_timestamp=' + toTimestamp;
		}
	}
});
