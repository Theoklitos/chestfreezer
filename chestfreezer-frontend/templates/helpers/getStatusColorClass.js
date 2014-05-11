define(['hbs/handlebars'], function(Handlebars) {	
	
	/*
	 * returns the appropriate colour (red or blue) based on the device state
	 */
	function getStatusColorClass(device, options) {
		if(device.state == 'off') {
			return "red-color";
		} else if(device.state == 'on') {
			return "blue-color";
		}		
		return "";
	}	
	
	Handlebars.registerHelper('getStatusColorClass', getStatusColorClass);	
	
	return getStatusColorClass
});