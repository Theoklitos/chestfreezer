define(['hbs/handlebars'], function(Handlebars) {	
	
	/*
	 * returns what text should be displayed when the device is on or off
	 */
	function getStatusText(device, options) {
		if(device['state']== 'off') {
			return "Off";
		} else if(device['state'] == 'on') {
			return "On";
		}		
		return "N/A";
	}
	
	Handlebars.registerHelper('getStatusText', getStatusText);
	
	return getStatusText;
});