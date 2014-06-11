define(['hbs/handlebars', 'utils'], function(Handlebars, utils) {	
	

	/*
	 * returns the unix timestamp as a human readable pretty datetime
	 */
	function prettyDateTime(timestamp, options) {
		if(timestamp > 0) {
			return utils.getUnixTimestampAsPrettyDateTime(timestamp);
		} else {
			return 'Undefined'
		}
	}
	
	Handlebars.registerHelper('prettyDateTime', prettyDateTime);
	
	return prettyDateTime
});