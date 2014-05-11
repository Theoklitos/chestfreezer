define(['hbs/handlebars'], function(Handlebars) {	
	
	/*
	 * returns the appropriate colour (red or blue) based on the device state
	 */
	function getStatusColorClass(device, options) {
		var style = "";
		if(device.state == 'off') {
			style = "red-color";
		} else if(device.state == 'on') {
			style = "blue-color";
		}		
		return style;
	}	
	
	Handlebars.registerHelper('getStatusColorClass', getStatusColorClass);	
	
	return getStatusColorClass
});
