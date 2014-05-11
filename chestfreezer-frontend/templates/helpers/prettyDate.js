define(['hbs/handlebars', 'utils'], function(Handlebars, utils) {	
	
	/*
	 * returns the unix timestamp as a human readable pretty date
	 */
	function prettyDate(timestamp, options) {
		return utils.getUnixTimestampAsPrettyDate(timestamp);	
	}	
	
	Handlebars.registerHelper('prettyDate', prettyDate);	
	
	return prettyDate
});