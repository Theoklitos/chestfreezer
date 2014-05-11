define(['hbs/handlebars'], function(Handlebars) {	
	
	/*
	 * if the master value is true, return "checked" so as to tick the checkbox. Return nothing otherwise.
	 */
	function shouldBeChecked(master, options) {		
		if(master === 'True') {
			return "checked";
		}
	}	
	
	Handlebars.registerHelper('shouldBeChecked', shouldBeChecked);	
	
	return shouldBeChecked
});
