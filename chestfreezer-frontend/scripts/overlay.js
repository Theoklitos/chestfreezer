/*
 * Contains methods that overlay the view
 */
define([ 'jquery' , 'bootbox' ], function($, bootbox) {
	return {
		
		/*
		 * displays an alert box using bootbox
		 */
		alert : function(message, callback) {
			bootbox.alert(message, callback);
		},

		/*
		 * Overlays the chart with a loading icon
		 */
		showLoadingOverlayChart : function(shouldShow) {
			this.showLoadingOverlay(shouldShow, $('#temperature-chart'), 'Reading temperatures...', 270, 160);
		},

		/*
		 * overlays the whole page with a loading icon, disabling everything
		 */
		showLoadingOverlayWholeScreen : function(shouldShow, overlayHeight) {
			if(overlayHeight == undefined) {
				overlayHeight = ($('#main-page').height() / 2) - 60;
			}
			this.showLoadingOverlay(shouldShow, $('#main-page'), 'Loading...', 130, overlayHeight);
		},

		/*
		 * Can be parameterized to display and overlay anywhere
		 */
		showLoadingOverlay : function(shouldShow, element, message, width, marginTop) {
			if (shouldShow) {
				var overlay = $('<div class="overlay"></div>');
				var spinner = $('<div class="spinner" style="width: ' + width + 'px; margin-top: ' + -marginTop + 'px">' + message
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