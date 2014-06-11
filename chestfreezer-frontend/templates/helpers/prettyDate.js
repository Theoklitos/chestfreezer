define(['hbs/handlebars', 'utils'], function(Handlebars, utils) {	
	
	/*
	 * returns the unix timestamp as a human readable pretty date (no time)
	 */
	function prettyDate(timestamp, options) {
		if(timestamp > 0) {
			return utils.getUnixTimestampAsPrettyDate(timestamp);
		} else {
			return 'Undefined'
		}
	}
	
	Handlebars.registerHelper('prettyDate', prettyDate);
	
	return prettyDate
});