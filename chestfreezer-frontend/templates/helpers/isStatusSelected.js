define(['hbs/handlebars'], function(Handlebars) {	
	
	/*
	 * returns "selected" if the value for the device should be shown in the dropdown selector
	 */
	function isStatusSelected(value, device, options) {		
		if(device['overridden'] == 'false') {			
			if(value == 'overridden') {return 'selected';}
		} else {
			if(value == device['state']) {return 'selected';}
		}	
	}
	
	Handlebars.registerHelper('isStatusSelected', isStatusSelected);
	
	return isStatusSelected;
});