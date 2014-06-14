({
	baseUrl: "scripts",
	out: "scripts/chestfreezer-built.js",
	name: "chestfreezer",
	optimize: "uglify2",
	paths : {
		'jquery' : 'lib/jquery.min',
		'bootstrap' : 'lib/bootstrap.min',
		'bootbox' : 'lib/bootbox.min',
		'globalize' : 'lib/globalize.min',
		'domReady' : 'lib/domReady',
		'chartjs' : 'lib/dx.chartjs',
		'canvasjs' : 'lib/canvasjs.min',
		'moment' : 'lib/moment.min',
		'bootstrap-datetimepicker' : 'lib/bootstrap-datetimepicker.min',
		'Base64' : 'lib/Base64',
		'hbs' : 'lib/hbs'
	},
	shim : {
		'domReady' : {
			deps : [ 'bootstrap' ]
		},
		'bootstrap' : {
			deps : [ 'jquery', 'moment', 'bootstrap-datetimepicker' ]
		},
		'Base64' : {
			exports : 'Base64'
		},
		'chartjs' : {
			deps : [ 'globalize', 'jquery' ]
		}
	},
	hbs : {
		templateExtension : 'html',
		helperPathCallback : function(name) {
			return '../templates/helpers/' + name + '.js';
		}
	}
})
