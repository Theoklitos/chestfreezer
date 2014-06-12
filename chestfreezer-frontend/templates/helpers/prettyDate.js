define(['hbs/handlebars', 'utils'], function(Handlebars, utils) {	
	
	/*
	 * returns the unix timestamp as a human readable pretty date or datetime
	 */
	function prettyDate(onlyDate, timestamp, options) {
		if(timestamp > 0) {
			if(onlyDate == 'date') {
				return utils.getUnixTimestampAsPrettyDate(timestamp);
			} else {
				return utils.getUnixTimestampAsPrettyDateTime(timestamp);
			}
		} else {
			return 'Undefined'
		}
	}
	
	Handlebars.registerHelper('prettyDate', prettyDate);
	
	return prettyDate
});