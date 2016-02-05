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
		zoom:7.3
	});

/*set up the feature styles*/
var featureLayer = new L.GeoJSON();
var defaultStyle = {
            color: "#2262CC",
            weight: 1,
            opacity: 0.6,
            fillOpacity: 0.1,
            fillColor: "#2262CC"
};

var boldStyle = {
            color: "#2262CC",
            weight: 3,
            opacity: 0.6,
            fillOpacity: 0.1,
            fillColor: "#2262CC"
};

function highlightFeature(e) {
    var layer = e.target;
    layer.setStyle({ // highlight the feature
        weight: 5,
        color: '#666',
        dashArray: '',
        fillOpacity: 0.6
    });
    if (!L.Browser.ie && !L.Browser.opera) {
        layer.bringToFront();
    }
    //map.info.update(layer.feature.properties); // Update infobox
}

function resetHighlight(e) {
    var layer = e.target;
    layer.setStyle(boldStyle);
    if (!L.Browser.ie && !L.Browser.opera) {
        layer.bringToFront();
    }
    //map.info.update(layer.feature.properties); // Update infobox
}


/*style each feature*/
var onEachProvinceFeature = function(feature, layer) {
	layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight
        //click: zoomToFeature,
        //pointToLayer: pointToLayer
     });
	
	layer.setStyle(boldStyle);
    //add text labels at the center of each feature
    var labelName = feature.properties.name;
    var iconsize = [50,10];
    /* Manual hack to shift the SFO province more to the right */
	if (feature.properties.nuts3 == 'SFO') {
       	iconsize = [0,10];
    }        
    //console.log(layer.getBounds().getCenter());
    var label = L.marker(layer.getBounds().getCenter(), {        	
    	icon: L.divIcon({
      		className: 'province-label',
       		html: labelName,
       		iconSize: iconsize})
        });
    label.addTo(map);
};

var onEachMunicipalityFeature = function(feature, layer) {		
	if (feature.properties && feature.properties.name) {
     	layer.bindPopup(feature.properties.name);
    }
    layer.setStyle(defaultStyle);
  
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
console.log(featureProvincesLayer);

var featureMunicipalitiesLayer = L.geoJson(bgmunicipalities, {
	onEachFeature: onEachMunicipalityFeature	
});

map.addLayer(featureMunicipalitiesLayer);
map.addLayer(featureProvincesLayer);