/*
 * Configuration for the chestfreezer app
 */
define([ 'jquery' ], function($) {
	return {
		rootUrl : '/chestfreezer/api',
		temperatureUpdateIntervalSeconds : 60,		
		instructionUpdateIntervalSeconds : 60,
		devicesUpdateIntervalSeconds : 15,
		daysPastToShowInChart : 1,
		showLoginForm : false,
		username : 'test-username',
		password : 'test-password',	
		
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







