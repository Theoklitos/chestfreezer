/*
 * Stores logging messages along with some wrapper functions 
 */
define([ 'jquery', 'utils' ], function($, utils) {
	return {
		logEvents : [],
		dontShowTemperatureEvents : false,
		
		/*
		 * will log the given message. Will also print to console
		 */
		log : function(message, isTempEvent) {
			console.log(message);
			if(isTempEvent == undefined) {
				isTempEvent = false;		
			}
			this.logEvents.push({
				message : utils.getNowPretyDateTime() + ' : ' + message,
				tempEvent : isTempEvent
				});						
		},
		
		/*
		 * returns all the messages logged so far
		 */
		getAll: function() {
			resultingHtml = '';
			for(n in this.logEvents) {
				event = this.logEvents[n];
				if(event.tempEvent == true && this.dontShowTemperatureEvents) {
					continue;
				}
				prefix = '\n';
				if(!resultingHtml) {
					prefix = '';
				}				
				resultingHtml += prefix + event.message;
			}
			return resultingHtml;
		}
	}
});
