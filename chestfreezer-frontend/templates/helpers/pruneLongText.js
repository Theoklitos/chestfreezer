define(['hbs/handlebars', 'utils'], function(Handlebars, utils) {	
	
	/*
	 * If the text is too long, returns a shortened version with a "..." at the end
	 */
	function pruneLongText(text, options) {		
		return utils.getPrunedText(text);
	}
	
	Handlebars.registerHelper('pruneLongText', pruneLongText);
	
	return pruneLongText;
});