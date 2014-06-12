/*
 * Configuration for the chestfreezer app
 */
define([ 'jquery' ], function($) {
	return {
		rootUrl : '/chestfreezer/api',
		temperatureUpdateIntervalSeconds : 60,
		stopTemperatureUpdates : false, // used to synchronize access to chart
		instructionUpdateIntervalSeconds : 60,
		devicesUpdateIntervalSeconds : 15,
		daysPastToShowInChart : 1,
		showLoginForm : true,
		username : 'test-username',
		password : 'test-password',	
		
		/*
		 * closure to get the following boolean value
		 */
		shouldStopTemperatureUpdates : function() {
			return this.stopTemperatureUpdates;
		},
		
		/*
		 * closure for returning the "seconds", after multiplying by 1000
		 */
		getTemperatureUpdateIntervalSeconds : function() {
			return this.temperatureUpdateIntervalSeconds * 1000;
		},
		
		/*
		 * as above
		 */
		getInstructionsUpdateIntervalSeconds : function() {			
			return this.instructionUpdateIntervalSeconds * 1000;
		},
		
		/*
		 * as above
		 */
		getDeviceUpdateIntervalSeconds : function() {			
			return this.devicesUpdateIntervalSeconds * 1000;
		}
	
	}
});







