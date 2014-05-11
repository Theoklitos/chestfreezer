define(['hbs/handlebars', 'model'], function(Handlebars, model) {	
	
	/*
	 * checks if the given instruction id equals the active instruction's one
	 */
	function isActiveInstruction(id, options) {
		if(model.active_instruction != undefined) {
			if(model.active_instruction.instruction_id == id) {
				return 'table-active-highlight';
			}
		} else {
			return ""
		}		
	}	
	
	Handlebars.registerHelper('isActiveInstruction', isActiveInstruction);	
	
	return isActiveInstruction
});