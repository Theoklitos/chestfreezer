/*
 * Various methods that connect to the view of the app
 */
define(['jquery', 'log', 'model', 'overlay', 'apiCaller', 'configuration', 'utils', 'bootbox', 'chartjs', 'canvasjs', 'hbs/handlebars', 'hbs!../templates/login', 
        'hbs!../templates/header', 'hbs!../templates/device', 'hbs!../templates/instructionsPanel', 'hbs!../templates/probePanel', 'hbs!../templates/logPanel', 
        'hbs!../templates/settingsPanel', 'hbs!../templates/beerTracker'], 
		function($, logger, model, overlay, api, configuration, utils, bootbox, chartjs, canvasjs, Handlebars, login, header, device, instructions, probes, 
				log, settings, beerTracker) {
  return {
	  
	  chart : {}, // reference to the canvasJS chart
	  showLogInterval : {}, // handle to stop the log monitor
	  overlay : overlay, // its convenient to have a reference here
	  
	  /*
	   * shows the main page and sets the username in the header
	   */
	  showMainPageForUser : function(givenUsername) {
		  $('#main-page').show();
		  $('#header').html(header({username : givenUsername}));
	  },	  
	  
	  /*
	   * displays an alert overlay
	   */
	  alert : function(message) {
		  overlay.alert(message);
	  },
	  
	  /*
	   * shows an overlay window with a prompt message, calls function with the user input
	   */
	  showPrompt : function(message, onSuccess) {
		  bootbox.prompt(message, function(result) {                
			  if (result === null) {                                             
			    // dismissed, do nothing                              
			  } else {
			    onSuccess(result);                          
			  }
		  });
	  },

	  /*
	   * initialize the temp gauge using the chartjs library
	   */
	  initializeGauge : function () {		  
		  $("#temperature-gauge").dxCircularGauge({			  
		  		scale : {
		  			majorTick : {
		  				color : 'black',
		  				tickInterval : 10
		  			},
		  			minorTick : {
		  				visible : true,
		  				color : 'black',
		  				tickInterval : 1
		  			},
		  			startValue : -20,
		  			endValue : 80
		  		},
		  		subvalueIndicator : {
		  			color : 'green'
		  		},
		  		subvalues : [],
		  		rangeContainer : {
		  			offset : 5,
		  			ranges : [ {
		  				startValue : -20,
		  				endValue : 0,
		  				color : 'blue'
		  			}, {
		  				startValue : 0,
		  				endValue : 80,
		  				color : 'red'
		  			} ]
		  		}
		  	});
	  },
	  
	  /*
	   * initializes and renders the canvas.js chart in our html. Also stores a reference.
	   */
	  initializeChart : function(chartData) {		  
		  unit = "℃";
		  var chart = new CanvasJS.Chart("temperature-chart", {
				zoomEnabled : true,
				title : {
					text : "Temperature Readings"
				},
				toolTip : {
					shared : true,					
				 	content: function(e) {
				 		var str = '' + new Date(e.entries[0].dataPoint.x)
				 		str = '<strong>' + str.substring(0, str.length-15) + '</strong>'
				        for (var i = 0; i < e.entries.length; i++){
				        	var probeName = e.entries[i].dataSeries.name;
				        	var hexColor = e.entries[i].dataSeries.color;
				        	str = str.concat('<br><span style="color:' + hexColor + '">' + probeName + '</span>: ' + e.entries[i].dataPoint.y + unit);
				        };
				        return (str);
				 	},
				},
				axisY : {
					suffix : ' ' + unit,
					includeZero : false
				},
				data : chartData
			});
			this.chart = chart; 
			chart.render();
	  },
	  	  
	  /*
	   * enables or disabels the temp override textarea + button 
	   */
	  enableTemperatureOverridePanel : function(state) {
		  $("#taget-temperature-textfield").prop("disabled", !state);
		  $("#taget-temperature-button").prop("disabled", !state);
		  if(!state) {
			  $("#taget-temperature-textfield").val('');
		  }
	  },
	  
	  /*
	   * sets the given celsius temperature on the temp gauge/dial
	   */
	  setCurrentTemperature : function(temperatureCelsius) {
		  var template = Handlebars.compile("<span>Current Temperature:</span> <strong>{{temperature}} &degC</<strong>");
		  $('#temperature-reading').html(template({temperature:temperatureCelsius}));		  
		  gauge = $('#temperature-gauge').dxCircularGauge('instance');
		  gauge.value(temperatureCelsius);		  
	  },
	  
	  /*
	   * Polls the server for the state of the heater + freezer and then updates the view (texts, dropdowns etc) using the template
	   */
	  updateDevices : function() {
		  api.updateDevices(function() {		  
			  freezerHtml = device({
				  status: model.devices['freezer'],
				  deviceName: 'Freezer'
			  });
			  $('#freezer-status').html(freezerHtml);
			  heaterHtml = device({
				  status: model.devices['heater'],
				  deviceName: 'Heater'
			  });
			  $('#heater-status').html(heaterHtml);
		  });
	  },
	  
	  /*
	   * calls the server to update both instructions & the target temperature 
	   */
	  updateInstructionsAndTargetTemperature : function() {
		  this.showInstructions();
		  this.updateTargetTemperature();
	  },
	  
	  /*
	   * gets the target temperature and updates the gauge as well as the status panel
	   */
	  updateTargetTemperature : function() {
		  reference = this;
		  api.getTargetTemperature(function(targetTemperature, isOverride) {			  
			  reference.enableTemperatureOverridePanel(isOverride)
			  $("#taget-temperature-checkbox").prop('checked', isOverride);
			  if(isOverride) {			  
				  $("#taget-temperature-textfield").val(targetTemperature);			  
			  }
			  if(targetTemperature) {		
				  $('#temperature-gauge').dxCircularGauge('instance').subvalues([targetTemperature]);
			  } else {
				  $('#temperature-gauge').dxCircularGauge('instance').subvalues([]);			  			  
			  }	
		  });
	  },
	  
	  /*
	   * calls the server to update the instructions, active and non-active, and shows all the instructions 
	   */
	  showInstructions : function() {		  
		  api.updateInstructions(function() {			  
			  if($('#instruction-menu-button').hasClass('active')) {
				  var template = instructions({instructions:model.instructions});		   
				  $('#content').html(template);			  
				  $('#datetime-from').datetimepicker({
					  pickTime: true
				  });
				  $('#datetime-to').datetimepicker({
					  pickTime: true
				  });
			  }
			  var text = 'No active instruction';		  
			  if(model.active_instruction != undefined) {
				  prettyUntil = utils.getUnixTimestampAsPrettyDate(model.active_instruction.to_timestamp);
				  text = 'Maintain ' + model.active_instruction.target_temperature_C + '℃ until ' + prettyUntil + '';
			  }
			  var template = Handlebars.compile('<span class="status-text instruction-text"><em>{{ instructionText }}</em></<span>');
			  $('#active-instruction').html(template({instructionText:text}));
		  });
	  },
	  
	  /*
	   * displays the error message in the appropriate part of the site
	   */
	  handleError : function(errorMessage) {
		  logger.log('Error: ' + errorMessage);	  	
		  $("#error-message-panel").addClass("alert alert-danger");
		  $("#error-message").html('<strong>' + errorMessage + '</strong>');
		  setTimeout(function() {
			  $("#error-message-panel").removeClass("alert alert-danger");
			  $("#error-message").html('');
		  }, 5000);	  	
	  },
	  
	  /*
	  /toggles a login form overlay that hides the whole page
	  */
	  showLoginForm : function(toggleState) {
		  if(toggleState) {
			  $('#login-form').append(login);
		  } else {
			  $('#login-form').hide();
		  }
	  },
	  
	  /*
	   * self-explanatory
	   */
	  scrollDown : function() {
		  $('html, body').animate({scrollTop: $(document).height()}, 'fast');
	  },
	  	  
	  /*
	   * highlights the given button, while removing highlight from the other ones
	   */
	  setActiveMenuButton : function(button) {		  
		  $('#content').html('');
		  $('.chestfreezer-menu-button').removeClass('active');
		  $(button).toggleClass('active');		  
		  // to avoid zombie events
		  $('.bootstrap-datetimepicker-widget').remove(); 
		  clearInterval(this.showLogInterval);		  
	  },
	  
	  /*
	   * sets the fields in the instruction form from the provided instruction object
	   */
	  setInstructionForm : function(instruction) {
		  //first the button
		  if(instruction == undefined) {
			  $('#save-instruction').html('Save');
			  instruction = {};
		  } else {
			  $('#save-instruction').html('Update');
		  }
		  $('#targetTemperature').val(instruction.target_temperature_C);
		  $('#description').val(instruction.description);
		  datetimeFrom = utils.getUnixTimestampAsPrettyDate(instruction.from_timestamp);
		  $('#datetime-from-value').val(datetimeFrom);
		  datetimeTo = utils.getUnixTimestampAsPrettyDate(instruction.to_timestamp);
		  $('#datetime-to-value').val(datetimeTo);		  
	  },
	  
	  /*
	   * applies a highlight to the given selected (clicked-upon) row  
	   */
	  setRowHighlighted : function(row, shouldToggle) {
		  if(shouldToggle) {
			  row.toggleClass('table-highlight').siblings().removeClass('table-highlight');
		  } else {
			  row.addClass('table-highlight').siblings().removeClass('table-highlight');
		  }
	  },
	  	  
	  /*
	   * updates probe information from the server and then displays them in the probe panel 
	   */
	  showProbes: function(onSuccess) {
		  api.updateProbeInfo(function() {
			  if($('#probe-menu-button').hasClass('active')) {
				  var template = probes({probes:model.probes});		   
				  $('#content').html(template);
			  }
			  if(onSuccess != undefined) {
				  onSuccess();
			  }
		  });		  	  
	  },
	  
	  /*
	   * returns a number of probe objects contructed from the data in the probe table
	   */
	  getProbesFromTable : function() {
		  result = [];
		  $('#probes-table-body tr').each(function() {
			  tds = $(this).children('td'); // children array
			  var isMaster = 'False';
			  if(tds[2].firstChild.checked) {
				  isMaster = 'True';
			  }
			  tableProbe = {
					  probe_id : tds[0].textContent,
					  name : tds[1].textContent,
					  master : isMaster,
			  }			  
			  result.push(tableProbe)			  		      
		  });
		  return result;
	  },
	  
	  /*
	   * displays the log panel 
	   */
	  showLog: function() {
		  reference = this;
		  if($('#log-menu-button').hasClass('active')) {
			  var template = log();		   
			  $('#content').html(template);			  
			  this.setLogTextareaText(logger.getAll());
			  this.showLogInterval = setInterval(function() {
				  try {
					  reference.refreshLog();
				  } catch(error) {
					  // swallow it. I cannot understand this bug.
				  }
			  }, 1000);			 
			  $('#dont-show-temp-updates').prop('checked', logger.dontShowTemperatureEvents);
		  }
	  },
	  
	  /*
	   * retrieves the setttings from the backend and displays them in the template
	   */
	  showSettings : function() {
		  api.getSettings(function(response) {			  
			  var settingsDisplay = {
				  store_temperature_interval_seconds: configuration.temperatureUpdateIntervalSeconds,
				  temperature_tolerance_C: response.temperature_tolerance_C,
				  instruction_interval_seconds: configuration.instructionUpdateIntervalSeconds,
				  devicesUpdateIntervalSeconds: configuration.devicesUpdateIntervalSeconds,
				  daysPastToShowInChart: configuration.daysPastToShowInChart,
				  databaseCurrentSize: response.database_size_MB,
				  databaseMaxSize: response.database_size_MB + response.database_free_size_MB
			  }
			  var template = settings({settings:settingsDisplay});		   
			  $('#content').html(template);  
		  });
	  },
	  
	  /*
	   * shows the beer tracker tab, with the beers-in-development, their history and all that
	   */
	  showBeerTracker: function(onSuccess) {
		  api.updateBeers(function() {
			  if($('#beertracker-menu-button').hasClass('active')) {
				  var template = beerTracker({beers:model.beers});				  		   
				  $('#content').html(template);
			  }
			  if(onSuccess != undefined) {
				  onSuccess();
			  }
			  $('#beer-table').find('.beer-date-cell').each(function (n) {
				  cell = $(this)
				  $(function () {
					  cell.datetimepicker({
						  pickTime: false
					  });
				  });
				  $(this).on("dp.show",function (e) {
					  $(this).siblings().filter(":first").click(); // to select the row
				  });
				  $(this).on("dp.change",function (e) {
					  var date = new Date(e.date._d);
					  var monthText = date.getMonth();
					  if(monthText < 10) {
						  monthText = '0' + monthText;
					  }					  
					  var formattedDate = date.getDate() + '/' + monthText + '/' + date.getFullYear();
					  $(this).html(formattedDate);					  
				  });
			  });			  
		  });		  
	  },	  
	  
	  /*
	   * sets the given text to the log textarea and scrolls all the way down 
	   */
	  setLogTextareaText: function(text) {
		  var logTextarea = $('#log-textarea');		  
		  logTextarea.val(text);
		  logTextarea.scrollTop(logTextarea[0].scrollHeight - logTextarea.height());
	  },
	  
	  /*
	   * refreshes  the log
	   */
	  refreshLog: function() {		  
		  this.setLogTextareaText(logger.getAll());
	  }	  
  }
});