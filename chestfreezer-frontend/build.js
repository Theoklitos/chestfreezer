({
	baseUrl: "scripts",
	out: "scripts/chestfreezer-built.js",
	name: "chestfreezer",
	optimize: "uglify2",
	paths : {
		'jquery' : 'http://ajax.googleapis.com/ajax/libs/jquery/2.1.0/jquery.min',
		'bootstrap' : '//netdna.bootstrapcdn.com/bootstrap/3.0.0/js/bootstrap.min',
		'bootbox' : 'lib/bootbox.min',
		'globalize' : 'http://ajax.aspnetcdn.com/ajax/globalize/0.1.1/globalize.min',
		'domReady' : 'lib/domReady',
		'chartjs' : 'http://cdn3.devexpress.com/jslib/13.2.9/js/dx.chartjs',
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
