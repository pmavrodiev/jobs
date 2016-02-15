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
		touchZoom:true,
		doubleClickZoom:false,
		boxZoom:false,
		bounceAtZoomLimits:false,
		keyboard:false,
		zoomControl:false,
		center:new L.LatLng(43.17, 25.4004),
		zoom:7.1
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

var municipality_BoldStyle = {
            color: "#2262CC",
            weight: 3,
            fillOpacity: 0.6,
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
var highlightedProvinceLayer;

/* Mouse events for municipality*/
function mouseoverMunicipality(e) {
	console.log("mouse over municipality");
	var layer = e.target;       
	// better safe than sorry
	if (d3plot_granularity == MUNICIPALITY) {
		layer.setStyle(municipality_BoldStyle);
		layer.feature.properties.is_highlighted = true;
	} 
}


function mouseclickMunicipality(e) {
	var layer = e.target;
	/*
	 * Since each municipality feature stores the _leaflet_id of
	 * its parent layer (province), we can get a handle to the parent
	 * via L.layerGroup.getLayer() API.
	 * We highlight the parent layer only if it is not currently highlighted. 
	 * After highlighting we update the highlightedProvinceLayer with the _leaflet_id 
	 * of the said parent	
	 */
	if (d3plot_granularity == MUNICIPALITY) {
    	var parentLayerID = layer.feature.properties.parentProvinceLayer;
    	if (parentLayerID) {
    		var parentLayer = featureProvincesLayer.getLayer(parentLayerID);
    		var provinceName = parentLayer.feature.properties.name;
    		var provinceNUTS3 = parentLayer.feature.properties.nuts3;
    		var municipalityNUTS4 = layer.feature.properties.nuts4;
    		var municipalityName = layer.feature.properties.name;
    	
    		var location = document.getElementById("location");
    		location.textContent = municipalityName;
    		var fileName = provinceNUTS3 + "." + municipalityNUTS4 + ".csv"; 
   			displayD3("/server/data/csv/" + fileName);
    	     	
    	}
    }   
};

function mouseoutMunicipality(e) {
	var layer = e.target;
	// better safe than sorry
	if (d3plot_granularity == MUNICIPALITY) {
		layer.setStyle(municipality_DefaultStyle);
		layer.feature.properties.is_highlighted = false;
	}	
};

function mouseoverProvince(e) {
	// better safe than sorry
	if (d3plot_granularity == PROVINCE || d3plot_granularity == COUNTRY) {
		console.log("province mouse over");
		this.setStyle(province_BoldStyle);
		this.feature.properties.is_highlighted = true;
    }
	
};

function mouseoutProvince(e) {
	// better safe than sorry
	if (d3plot_granularity == PROVINCE || d3plot_granularity == COUNTRY) {
		console.log("province mouse out");
		this.setStyle(province_DefaultStyle);
		this.feature.properties.is_highlighted = false;
    }
	
};

function mouseclickProvince(e) {
	if (d3plot_granularity == PROVINCE || d3plot_granularity == COUNTRY) {
    	var provinceName = this.feature.properties.name;
    	var provinceNUTS3 = this.feature.properties.nuts3;

    	var location = document.getElementById("location");
    	location.textContent = provinceName;
    	var fileName = provinceNUTS3 + ".csv"; 
   		displayD3("/server/data/csv/" + fileName);	     	
    }
};
/*style each feature*/

var onEachProvinceFeature = function(feature, layer) {
	layer.setStyle(province_DefaultStyle);
    //add text labels at the center of each feature
    var labelName = feature.properties.name;
    var iconsize = [50,10];
    
    /* Manual hack to shift the SFO province more to the right */
	if (feature.properties.nuts3 == 'SFO') {
       	iconsize = [0,10];
    }
    
    feature.properties.is_highlighted = false;
    
    layer.on({
        mouseover: mouseoverProvince,
        mouseout: mouseoutProvince,
        click: mouseclickProvince,
        //pointToLayer: pointToLayer
    });

    
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
	
	feature.properties.is_highlighted = false;
	
    layer.on({
        mouseover: mouseoverMunicipality,
        mouseout: mouseoutMunicipality,
        click: mouseclickMunicipality,
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


var featureMunicipalitiesLayer = L.geoJson(bgmunicipalities, {
	onEachFeature: onEachMunicipalityFeature	
});

map.addLayer(featureMunicipalitiesLayer);
map.addLayer(featureProvincesLayer);


/*set up special controls
 *  
 * Code adapted from http://opendata.yurukov.net/educ/map/
 * 
 * */

var INACTIVE = ""; var ACTIVE = "0.3";
var COUNTRY = 0; var PROVINCE = 1; var MUNICIPALITY = 2;
var d3plot_granularity = COUNTRY;
var d3plot_filename = ""; // curently displayed region

// just a helper function
function flipEnabled(type) {
		
	var switch_1 = document.getElementById("switch_1");
	var switch_2 = document.getElementById("switch_2");
	var switch_3 = document.getElementById("switch_3");
	
	switch_1.is_active=false;
	switch_2.is_active=false;
	switch_3.is_active=false;
	switch_1.style.opacity = INACTIVE;
	switch_2.style.opacity = INACTIVE;
	switch_3.style.opacity = INACTIVE;
	
	var switch_arr = {1: switch_1, 2: switch_2, 3: switch_3};
	
	switch_arr[type].is_active=true;
	switch_arr[type].style.opacity = ACTIVE;
}

L.Control.DataSwitch = L.Control.extend({
	options: {
		collapsed: true,
		position: 'topleft',
		autoZIndex: true
	},

	initialize: function (dataValTypes, options) {
		L.setOptions(this, options);
		this._types = dataValTypes;
	},

	onAdd: function (map) {
		var leaflet_control = document.createElement("div");
		leaflet_control.className = "leaflet-control";
		
		for (var i in this._types) {
			var switchDiv = document.createElement("div");
			switchDiv.id = "switch_" + this._types[i].type;
			switchDiv.className = "leaflet-control-layers dataswitch";
			switchDiv.is_active = this._types[i].is_active;
			switchDiv.style.opacity=(this._types[i].is_active) ? ACTIVE : INACTIVE;
			
			switchDiv.addEventListener("click", function(e){
				// e.target is the <img> element
				parentDiv = e.target.parentNode;
    	        if (e.target.data.type == 1 && !parentDiv.is_active) {
    	        	if (d3plot_filename != "/server/data/csv/all.csv") {
    	        		displayD3("/server/data/csv/all.csv");
						var location = document.getElementById("location");
    		        	location.textContent = "България";
    		        }
    		        // enable this control and disable the other two controls
    			    // including adjusting their opacities
    			    flipEnabled(e.target.data.type);
    			    d3plot_granularity = COUNTRY;
    			    featureProvincesLayer.bringToFront();
    			    featureMunicipalitiesLayer.bringToBack();
					return;
    	        }
    	        else if (e.target.data.type == 2) {
    	        	d3plot_granularity = PROVINCE;
    	        	featureProvincesLayer.bringToFront();
    	        }
    	        else if (e.target.data.type == 3) {
    	        	d3plot_granularity = MUNICIPALITY;
    	        	featureMunicipalitiesLayer.bringToFront();
    	        }
    	        flipEnabled(e.target.data.type);
				return;    	        
    	    });
			
			var image = document.createElement("img");
			image.className = "control-button";
			image.src = this._types[i].src;
			image.alt = this._types[i].title;
			image.title = this._types[i].title;
			image.data = {"type": this._types[i].type, "title":this._types[i].title };
			
			switchDiv.appendChild(image);
			leaflet_control.appendChild(switchDiv);
		}
		document.getElementsByClassName("leaflet-control-container")[0].appendChild(leaflet_control);
			/*
		
			$("<div id='switch_"+this._types[i].type+"' class='leaflet-control-layers dataswitch' "+
			(this._active==this._types[i].type?"style='opacity:0.3;'":"")+">"+
			"<img src='" + this._types[i].src + "'"+
			" alt='" + this._types[i].title + "' title='" + this._types[i].title + "'/></div>")	
			.data("type",this._types[i].type)
			.data("control",this)
			.click(function() { 
				draw($(this).data("type")); 
				$(this).fadeTo(200,0.3);
				$("#switch_"+$(this).data("control")._active).fadeTo(200,1);
				$(this).data("control")._active=$(this).data("type");
			})
			.appendTo(container);
			*/
		return leaflet_control;
	}
});

/* add the controls */

map.addControl(new L.Control.DataSwitch([
	{"title":"Show statistics for whole country",
	  					src:'server/res/img/whole_country.png',type:1, is_active:true},
	{"title":"Show statistics for provinces",
	  					src:"/server/res/img/provinces.png",type:2, is_active:false},
	{"title":"Show statistics for municipalities",
	  					src:"server/res/img/municipalities.png",type:3, is_active:false}],
	{"default":4}));


