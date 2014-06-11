/*
 * Contains methods that overlay the view
 */
define([ 'jquery' , 'bootbox' ], function($, bootbox) {
	return {
		
		/*
		 * displays an alert box using bootbox
		 */
		alert : function(message) {
			bootbox.alert(message);
		},

		/*
		 * Overlays the chart with a loading icon
		 */
		showLoadingOverlayChart : function(shouldShow) {
			this.showLoadingOverlay(shouldShow, $('#temperature-chart'), 'Reading temperatures...', 270, 200);
		},

		/*
		 * overlays the whole page with a loading icon, disabling everything
		 */
		showLoadingOverlayWholeScreen : function(shouldShow) {
			this.showLoadingOverlay(shouldShow, $('#main-page'), 'Loading...', 130, 230);
		},

		/*
		 * Can be parameterized to display and overlay anywhere
		 */
		showLoadingOverlay : function(shouldShow, element, message, width, top) {
			if (shouldShow) {
				var overlay = $('<div class="overlay"></div>');
				var spinner = $('<div class="spinner" style="width: ' + width + 'px; top: ' + top + 'px">' + message
						+ '</div>');
				spinner.append($('<span class="glyphicon glyphicon-refresh"></span>'));
				element.after(spinner);
				element.after(overlay);
			} else {
				element.siblings('.overlay').remove();
				element.siblings('.spinner').remove();
			}
		},

	}
});