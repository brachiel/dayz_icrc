// Thanks to Solanum for all this

var map = {markerEditable: true};
var mapBounds = new OpenLayers.Bounds( 0.0, -13669.0, 16660.0, 0.0);
var mapMinZoom = 1;
var mapMaxZoom = 7;

var mapCenter = new OpenLayers.Geometry.Point( -13669/2, 16660/2 );
//var mapCenter = mapBounds.getCenterLonLat();

// avoid pink tiles
OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
OpenLayers.Util.onImageLoadErrorColor = "transparent";

function init() {																						
	var options = {
		controls: [],
		maxExtent: mapBounds,
		maxResolution: 128,
		numZoomLevels: 8
	};
	
	// Save settings to the map if there are any, already
	var map_settings = map;
	
	// Create the map objects
    map = new OpenLayers.Map('map', options);
    
    // Copy the settings from the old map object to the new one.
    for (var attr in map_settings) { if (! map_settings.hasOwnProperty(attr)) continue;
    	map[attr] = map_settings[attr];
    }
    
    var layer = new OpenLayers.Layer.TMS( "TMS Layer","",
        {  url: '', serviceVersion: '.', layername: '.', alpha: true,
			type: 'png', getURL: overlay_getTileURL 
		});
    map.addLayer(layer);
	map.zoomToExtent( mapBounds );	

    map.addControl(new OpenLayers.Control.PanZoomBar());
    //map.addControl(new OpenLayers.Control.MousePosition());
    map.addControl(new OpenLayers.Control.MouseDefaults());
    map.addControl(new OpenLayers.Control.KeyboardDefaults());
    
    var style_mark = OpenLayers.Util.extend();

	style_mark.graphicWidth = 21;
	style_mark.graphicHeight = 25;
	style_mark.graphicXOffset = -11;
	style_mark.graphicYOffset = -23;
	style_mark.externalGraphic = baseMapDataURL + 'marker.png'
	style_mark.title = "Drag this to your location.";

    var vectorLayer = new OpenLayers.Layer.Vector("Location marker");

    var marker = mapCenter;
    var feature = new OpenLayers.Feature.Vector(mapCenter,null,style_mark);
	
	map.addLayer(vectorLayer);
	map.setCenter(new OpenLayers.LonLat(marker.x, marker.y), 2);
    vectorLayer.addFeatures([ feature ]);
    
    controls = { drag: new OpenLayers.Control.DragFeature(vectorLayer, {'onDrag': map.onCompleteMove} ) }
   	map.addControl(controls['drag']);
    
    if (map.markerEditable)
    	controls['drag'].activate();

	map.setMedicMarker = function(lon, lat){
		console.log("set marker", lon, lat);
		
		feature.move(new OpenLayers.LonLat(lon, lat));
	}
	
	map.events.register("click", vectorLayer, function(e) {
		if (! map.markerEditable) return;
		
		var lonlat = map.getLonLatFromPixel(e.xy);
		
		map.setMedicMarker(lonlat.lon, lonlat.lat);
		
		map.sendMarkerToPage(lonlat);
	});
	
	map.sendMarkerToPage = function(lonlat) {
		$("#map").trigger("markerset", [Math.floor(lonlat.lon), Math.floor(lonlat.lat)]);
	}
	
	map.onMoveComplete = function(feature) {
		map.sendMarkerToPage(feature.lonlat);
	}
}

function overlay_getTileURL(bounds) {
    var res = this.map.getResolution();
    var x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
    var y = Math.round((bounds.bottom - this.maxExtent.bottom) / (res * this.tileSize.h));
    var z = this.map.getZoom();
    
	if (x >= 0 && y >= 0) {
		return baseMapDataURL + z + "/" + x + "/" + y + "." + this.type;		
	} else {
        return "img/none.png";
	}
}


$(document).ready(function(){
	init();
});

