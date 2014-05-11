/*
 * Various methods that connect to the view of the app
 */
define(['jquery', 'log', 'utils', 'bootbox', 'chartjs', 'canvasjs', 'hbs/handlebars', 'hbs!../templates/login', 'hbs!../templates/header', 'hbs!../templates/device', 
        'hbs!../templates/instructionsPanel', 'hbs!../templates/probePanel', 'hbs!../templates/logPanel'], 
		function($, logger, utils, bootbox, chartjs, canvasjs, Handlebars, login, header, device, instructions, probes, log) {
  return {
	  
	  chart : {}, // reference to the canvasJS chart
	  showLogInterval : {}, // handle to stop the log monitor
	  
	  /*
		 * displays an alert box using bootbox
		 */
	  alert : function(message) {
		  bootbox.alert(message);
	  },
	  
	  /*
		 * shows the main page and sets the username in the header
		 */
	  showMainPageForUser : function(givenUsername) {
		  $('#main-page').show();
		  $('#header').html(header({username : givenUsername}));
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
	   * initializes and reders the canvas.js chart, also stored a reference
	   */
	  initializeChart : function(chartData) {		  
		  var chart = new CanvasJS.Chart("temperature-chart", {
				zoomEnabled : true,
				title : {
					text : "Temperature Readings"
				},
				toolTip : {
					shared : true
				},
				axisY : {
					suffix : ' ℃',
					includeZero : false
				},
				data : chartData
			});
			this.chart = chart; 
			chart.render();
	  },
	  
	  /*
	   * displays the target temp information in the gauge and the status panel
	   */
	  setTargetTemperature : function(targetTemperature, isOverride) {
		  this.enableTemperatureOverridePanel(isOverride)
		  $("#taget-temperature-checkbox").prop('checked', isOverride);
		  if(isOverride) {			  
			  $("#taget-temperature-textfield").val(targetTemperature);			  
		  }
		  if(targetTemperature) {		
			  $('#temperature-gauge').dxCircularGauge('instance').subvalues([targetTemperature]);
		  } else {
			  $('#temperature-gauge').dxCircularGauge('instance').subvalues([]);			  			  
		  }			  
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
	   * updates the text and the dropdown menu of the heater + freezer html
	   */
	  updateDevices : function(deviceJson) {		  		  
		  freezerHtml = device({
			  status: deviceJson['freezer'],
			  deviceName: 'Freezer'
		  });
		  $('#freezer-status').html(freezerHtml);
		  heaterHtml = device({
			  status: deviceJson['heater'],
			  deviceName: 'Heater'
		  });
		  $('#heater-status').html(heaterHtml);
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
	   * highlights the given button, while removing highlight from the other ones
	   */
	  setActiveMenuButton : function(button) {
		  $('#content').html('');
		  $('.chestfreezer-menu-button').removeClass('active');
		  $(button).toggleClass('active');		  
		  // to avoid zombie events
		  $( ".bootstrap-datetimepicker-widget dropdown-menu" ).remove(); 
		  clearInterval(this.showLogInterval);
		  
	  },
	  
	  /*
	   * sets the fields in the instruction form from the given instruction object
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
	   * applies a highlight to the given row in the instructions table 
	   */
	  setInstructionRowHighlighted : function(row) {
		  row.toggleClass('table-highlight').siblings().removeClass('table-highlight');
	  },
	  
	  /*
	   * displays the instruction panel with the given instructions as a table 
	   */
	  showInstructions : function(allInstructions) {		  
		  if($('#instruction-menu-button').hasClass('active')) {
			  var template = instructions({instructions:allInstructions});		   
			  $('#content').html(template);			  
			  $('#datetime-from').datetimepicker();
			  $('#datetime-to').datetimepicker();
		  }		  
	  },
	  
	  /*
	   * displays the probe panel 
	   */
	  showProbes: function(allProbes) {		  
		  if($('#probe-menu-button').hasClass('active')) {
			  var template = probes({probes:allProbes});		   
			  $('#content').html(template);
		  }		  
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
				  reference.refreshLog();
			  }, 1000);
		  }		  
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
	  },
	  
	  /*
	   * displays the given instruction as the "active" one
	   */
	  displayActiveInstruction : function(activeInstruction) {		  
		  var text = 'No active instruction';
		  if(activeInstruction != undefined) {
			  prettyUntil = utils.getUnixTimestampAsPrettyDate(activeInstruction.to_timestamp);
			  text = 'Will maintain ' + activeInstruction.target_temperature_C + '℃ until ' + prettyUntil + '';
		  }
		  var template = Handlebars.compile('<span class="status-text instruction-text"><em>{{ instructionText }}</em></<span>');
		  $('#active-instruction').html(template({instructionText:text}));		  
	  }
  }
});








