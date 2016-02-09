//Map centering taken from http://opendata.yurukov.net/educ/map/
/*set up the map*/
var map = L.map('map', {
		maxBounds:new L.LatLngBounds(new L.LatLng(40.2711, 20.4565),new L.LatLng(45.1123, 30.3442)),
		minZoom:7,
		maxZoom:11,
		fullscreenControl: true,
		fullscreenControlOptions: {
			title: "На цял екран",
			forceSeparateButton:true
		},
		dragging:true,
		touchZoom:false,
		doubleClickZoom:false,
		boxZoom:false,
		bounceAtZoomLimits:false,
		keyboard:false,
		zoomControl:false,
		center:new L.LatLng(42.6917, 25.4004),
		zoom:8
	});

/*set up the feature styles*/
var featureLayer = new L.GeoJSON();
var municipality_DefaultStyle = {
            color: "#2262CC",
            weight: 1,
            opacity: 0.6,
            fillOpacity: 0.1,
            fillColor: "#2262CC"
};

var province_DefaultStyle = {
            color: "#2262CC",
            weight: 3,
            opacity: 0.6,
            fillOpacity: 0.1,
            fillColor: "#2262CC"
};

var province_BoldStyle = { // highlight the feature
        weight: 5,
        color: '#2262CC',
        dashArray: '',
        fillOpacity: 0.6
 };


//stores the _leaflet_id of the province layer currently highlighted
var highlightedProvinceLayer = new Array(1);

/* Mouse events for municipality*/
function mouseoverMunicipality(e) {
	var layer = e.target;       
	console.log('mouseover'); 
	/*
	 * Since each municipality feature stores the _leaflet_id of
	 * its parent layer (province), we can get a handle to the parent
	 * via L.layerGroup.getLayer() API.
	 * We highlight the parent layer only if it is not currently highlighted. 
	 * After highlighting we update the highlightedProvinceLayer with the _leaflet_id 
	 * of the said parent	
	 */
	
    var parentLayerID = layer.feature.properties.parentProvinceLayer;
    if (parentLayerID) {
    	if (highlightedProvinceLayer[0] && parentLayerID == highlightedProvinceLayer[0]) {
    		//var parentLayer=featureProvincesLayer.getLayer(parentLayerID);
    		//parentLayer.setStyle(province_BoldStyle);
    		//parentLayer.bringToFront();
    		//do nothing
    	}
    	else {
    		//remove the currently highligthed Province layer
    		if (highlightedProvinceLayer[0]) {
    			var  currentlyHighlighted = featureProvincesLayer.getLayer(highlightedProvinceLayer[0]);
    			currentlyHighlighted.setStyle(province_DefaultStyle);
    			currentlyHighlighted.bringToBack();
    		}
    		//highlight the new Province layer
    		var parentLayer=featureProvincesLayer.getLayer(parentLayerID);
    		parentLayer.setStyle(province_BoldStyle);
    		highlightedProvinceLayer[0] = parentLayerID;
    		//parentLayer.bringToFront();
    	}    	
    }    
}

function mouseoutMunicipality(e) {
	console.log('mouseout');
	var layer = e.target; 
};


/*style each feature*/

var onEachProvinceFeature = function(feature, layer) {
	layer.setStyle(province_DefaultStyle);
    //add text labels at the center of each feature
    var labelName = feature.properties.name;
    var iconsize = [50,10];
    console.log(feature.properties.name+";"+feature.properties.nuts3);
    /* Manual hack to shift the SFO province more to the right */
	if (feature.properties.nuts3 == 'SFO') {
       	iconsize = [0,10];
    }
    var label = L.marker(layer.getBounds().getCenter(), {        	
    	icon: L.divIcon({
      		className: 'province-label',
       		html: labelName,
       		iconSize: iconsize}),
       	clickable:false,
       	keyboard:false,
       	zIndexOffset:-1000
        });
    label.addTo(map);
};

var onEachMunicipalityFeature = function(feature, layer) {
	/* find the province feature to which this municipality belongs*/
	for (l=0; l < featureProvincesLayer.getLayers().length; l++) {
		provinceLayer = featureProvincesLayer.getLayers()[l];
		if (provinceLayer.feature && provinceLayer.feature.properties.nuts3 == feature.properties.nuts3) {
			feature.properties.parentProvinceLayer = provinceLayer._leaflet_id;
		}
	}	
	
    layer.on({
        //mouseover: highlightFeature,
        mouseover: mouseoverMunicipality,
        mouseout: mouseoutMunicipality,
        //click: zoomToFeature,
        //pointToLayer: pointToLayer
    });

	if (feature.properties && feature.properties.name) {
     	layer.bindPopup(feature.properties.name);
    }
    layer.setStyle(municipality_DefaultStyle);
  
    //add text labels at the center of each feature
    var labelName = feature.properties.name;
    var label = L.marker(layer.getBounds().getCenter(), {        	
    	icon: L.divIcon({
      		className: 'municipality-label',
       		html: labelName,
       		iconSize: [0, 0]})
       });
    //label.addTo(map);  
};

var featureProvincesLayer = L.geoJson(bgprovinces, {
	onEachFeature: onEachProvinceFeature
});

map.addLayer(featureProvincesLayer);


var featureMunicipalitiesLayer = L.geoJson(bgmunicipalities, {
	onEachFeature: onEachMunicipalityFeature	
});

map.addLayer(featureMunicipalitiesLayer);


/*Mouse events for the map*/
map.on('move', function (e) {
	console.log(map.getPanes());
	
});