  var map;
  var mapBounds = new OpenLayers.Bounds( 0.0, -13669.0, 16660.0, 0.0);
  var mapMinZoom = 0;
  var mapMaxZoom = 7;
  // avoid pink tiles
  OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
  OpenLayers.Util.onImageLoadErrorColor = "transparent";

  var vectorLayer;
  
  OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {                
	defaultHandlerOptions: {
	'single': true,
	'double': false,
	'pixelTolerance': 0,
	'stopSingle': false,
	'stopDouble': false
	},

	initialize: function(options) {
	  this.handlerOptions = OpenLayers.Util.extend({}, this.defaultHandlerOptions);
	  OpenLayers.Control.prototype.initialize.apply(this, arguments); 
	  this.handler = new OpenLayers.Handler.Click(this, {'click': this.trigger}, this.handlerOptions);
	}, 

	trigger: function(e) {
	  var lonlat = map.getLonLatFromPixel(e.xy);
	  
	  $("#map").trigger("markerset", [Math.floor(lonlat.lat), Math.floor(lonlat.lon)]);
	}
});


  $(document).ready(function(){
  /*
	resize();
  	$(window).resize(resize);
*/

	var options = {
			maxExtent: new OpenLayers.Bounds( 0.0, -13669.0, 16660.0, 0.0 ),
			maxResolution: 128.000000,
			numZoomLevels: 8
	};
	map = new OpenLayers.Map('map', options);
	var layer = new OpenLayers.Layer.TMS( "TMS Layer","",
		{ url: '', serviceVersion: '.', layername: '.', alpha: true, type: 'png', getURL: overlay_getTileURL });
	map.addLayer(layer);
	map.zoomToExtent( mapBounds );

	var click = new OpenLayers.Control.Click();
	map.addControl(click);
	click.activate();

	/* Add vector layer */
	vectorLayer = new OpenLayers.Layer.Vector("Overlay");

	vectorLayer.setMedicMarker = function(x,y) {
		if (vectorLayer.medicMarker)
			vectorLayer.removeFeatures(vectorLayer.medicMarker);

		vectorLayer.medicMarker = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(x, y), {'x': x, 'y': y},
									{externalGraphic: baseMapDataURL + 'marker.png', graphicHeight: 28, graphicWidth: 33});

		vectorLayer.addFeatures(vectorLayer.medicMarker);
	}

	map.addLayer(vectorLayer);
  });

  function overlay_getTileURL(bounds) {
	var res = this.map.getResolution();
	var x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
	var y = Math.round((bounds.bottom - this.maxExtent.bottom) / (res * this.tileSize.h));
	var z = this.map.getZoom();
	if (x >= 0 && y >= 0) {
	  return baseMapDataURL + z + "/" + x + "/" + y + "." + this.type;
	} else {
	  return "http://www.maptiler.org/img/none.png";
	}
  }

/*
  function resize() {
	var map = $("#map");
	var header = $("#header");
	if (! header) return;
	var subheader = $("#subheader");

	map.width($(document).width());
	map.height($(document).height());

	header.width($(document).width());
	subheader.width($(document).width());

	if (map.updateSize) { 
		map.updateSize(); 
	};
  }
*/

