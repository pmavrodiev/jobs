

// Breadcrumb dimensions: height, spacing, width of tip/tail.
var b = {
   h: 30, s: 3, t: 10
};

// Set-up the colors
all_colors = d3.scale.category20c();
var color_map = {};

// Total size of all segments; we set this later, after loading the data.
var totalSize = 0; 

var vis2 = d3.select("#chart").append("svg:svg")
					.attr("id", "d3_svg_container");
// Dimensions of arcs.
var width = parseInt(d3.select("#d3_svg_container").style("width"), 10);
var height = parseInt(d3.select("#d3_svg_container").style("height"), 10);
var radius = Math.min(width, height) / 2;
	
var partition = d3.layout.partition()
    .size([2 * Math.PI, radius * radius])
    .value(function(d) { return d.size; });


var arc = d3.svg.arc()
    			.startAngle(function(d) { return d.x; })
    			.endAngle(function(d) { return d.x + d.dx; })
   		 		.innerRadius(function(d) { return Math.sqrt(d.y); })
   		 		.outerRadius(function(d) { return Math.sqrt(d.y + d.dy); });

var vis = 0;

// Add the svg area.
var trail = d3.select("#job_breakdown").append("svg:svg")
      .attr("id", "trail");
// Add the label at the end, for the percentage.
trail.append("svg:text")
    .attr("id", "endlabel")
    .style("fill", "#000");
 


function tearDown() {
	vis2.select("g").remove();
}


/* Main function called from the outside */
function displayD3(filename) {
	// tear down the existing svg objects
	tearDown();

	vis = vis2.append("svg:g")
    			.attr("id", "container")
    			.attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

    // Bounding circle underneath to make it easier to detect
    // when the mouse leaves the parent g.
	vis.append("svg:circle")
    	  .attr("r",  0.7 * radius)
      	  .attr("id", "circle")
          .style("opacity", 0);

	// Use d3.text and d3.csv.parseRows so that we do not need to have a header
	// row, and can receive the csv as an array of arrays.
	d3.text(filename, function(text) {
  				var csv = d3.dsv(";", "text/plain").parseRows(text);
  				var json = buildHierarchy(csv);
 			 	createVisualization(json);
	});
	d3plot_filename = filename;
}

// Take a 2-column CSV and transform it into a hierarchical structure suitable
// for a partition layout. The first column is a sequence of step names, from
// root to leaf, separated by hyphens. The second column is a count of how 
// often that sequence occurred.
function buildHierarchy(csv) {
  var root = {"name": "root", "children": []};
  for (var i = 0; i < csv.length; i++) {
    var sequence = csv[i][0];
    var size = +csv[i][1];
    if (isNaN(size)) { // e.g. if this is a header row
      continue;
    }
    var parts = sequence.split("-");
    var currentNode = root;
    for (var j = 0; j < parts.length; j++) {
      var children = currentNode["children"];
      var nodeName = parts[j];
      var childNode;
      if (j + 1 < parts.length) {
   // Not yet at the end of the sequence; move down the tree.
 	var foundChild = false;
 	for (var k = 0; k < children.length; k++) {
 	  if (children[k]["name"] == nodeName) {
 	    childNode = children[k];
 	    foundChild = true;
 	    break;
 	  }
 	}
  // If we don't already have a child node for this branch, create it.
 	if (!foundChild) {
 	  childNode = {"name": nodeName, "children": []};
 	  children.push(childNode);
 	}
 	currentNode = childNode;
      } else {
 	// Reached the end of the sequence; create a leaf node.
 	childNode = {"name": nodeName, "size": size};
 	children.push(childNode);
      }
    }
  }
  return root;
};



// Main function to draw and set up the visualization, once we have the data.
function createVisualization(json) {
  
  // Calculate the colors for each category
  var all_categories = getNodeNames(json);
  for (var name=0; name < all_categories.length; name++) {
  	color_map[all_categories[name]] = all_colors(name);
  }
  
 // For efficiency, filter nodes to keep only those large enough to see.
  var nodes = partition.nodes(json)
      .filter(function(d) {
      return (d.dx > 0.005); // 0.005 radians = 0.29 degrees
      });

  var path = vis.data([json]).selectAll("path")
      .data(nodes)
      .enter().append("svg:path")
      .attr("display", function(d) { 
      	// do not display the root node at depth 0
      	return d.depth ? null : "none"; 
       })
      .attr("d", arc)
      .attr("fill-rule", "evenodd")
      .style("fill", function(d) { return color_map[d.name]; })
      .style("opacity", 1)
      .on("mouseover", mouse_over);

  // Add the mouseleave handler to the bounding circle.
  d3.select("#container").on("mouseleave", mouse_leave);


  // Get total size of the tree = value of root node from partition.
  totalSize = path.node().__data__.value;
 };

// Fade all but the current sequence, and show it in the breadcrumb trail.
function mouse_over(d) {

  var percentage = (100 * d.value / totalSize).toPrecision(3);
  var percentageString = percentage + "%";
  if (percentage < 0.1) {
    percentageString = "< 0.1%";
  }
  
  d3.select("#percentage")
      .html(percentageString);
      
  d3.select("#number")
  	  .html(Math.round(d.value,1));

  d3.select("#stats").
  	style("visibility", "");
  	  
  
  var sequenceArray = getAncestors(d);
  updateBreadcrumbs(sequenceArray, percentageString);

  // Fade all the segments.
  d3.select("#chart").selectAll("path")
      .style("opacity", 0.4);

  // Then highlight only those that are an ancestor of the current segment.
  d3.select("#chart").selectAll("path")
      .filter(function(node) {
                return (sequenceArray.indexOf(node) >= 0);
              })
      .style("opacity", 1);
}

// Restore everything to full opacity when moving off the visualization.
function mouse_leave(d) {

  // Hide the breadcrumb trail
  d3.select("#trail")
      .style("visibility", "hidden");

  // Deactivate all segments during transition.
  d3.select("#chart").selectAll("path").on("mouseover", null);

  // Transition each segment to full opacity and then reactivate it.
  d3.select("#chart").selectAll("path")
      .transition()
      .duration(500)
      .style("opacity", 1)
      .each("end", function() {
              d3.select(this).on("mouseover", mouse_over);
            });
  
  d3.select("#stats")
  		.style("visibility", "hidden");

}

// Given a node in a partition layout, return an array of all of its ancestor
// nodes, highest first, but excluding the root.
function getAncestors(node) {
  var path = [];
  var current = node;
  while (current.parent) {
    path.unshift(current);
    current = current.parent;
  }
  return path;
  
}


function getNodeNames(tree) {
	var children = tree.children;
    var children_names = [];
    
	if (!children) {return [];}
	
	for (var i=0; i < children.length; i++) {
		var front = children[i];
		children_names.push(front.name);
		children_names = children_names.concat(getNodeNames(front));
	}
	return children_names;
}


// Generate a string that describes the points of a breadcrumb polygon.
function breadcrumbPoints(d, i) {
  var w = getTextWidth(d.name);
  var points = [];
  points.push("0,0");
  points.push(w + ",0");
  points.push(w + b.t + "," + (b.h / 2));
  points.push(w + "," + b.h);
  points.push("0," + b.h);
  if (i > 0) { // Leftmost breadcrumb; don't include 6th vertex.
    points.push(b.t + "," + (b.h / 2));
  }
  return points.join(" ");
 
}

// Update the breadcrumb trail to show the current sequence and percentage.
function updateBreadcrumbs(nodeArray, percentageString) {
 
  // Data join; key function combines name and depth (= position in sequence).
  var g = d3.select("#trail")
      .selectAll("g")
      .data(nodeArray, function(d) { return d.name + d.depth; });

  // Add breadcrumb and label for entering nodes.
  var entering = g.enter().append("svg:g");

  entering.append("svg:polygon")
      .attr("points", breadcrumbPoints)
      .style("fill", function(d) { return color_map[d.name]; });

  entering.append("svg:text")
      .attr("x", function(d, i) {
        var w = getTextWidth(d.name);
      	return (w + b.t) / 2;
      	})
      .attr("y", b.h / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", "middle")
      .text(function(d) { return d.name; });

  // Set position for entering and updating nodes.
  g.attr("transform", function(d, i) {
  	var w = 0;
  	// Sum up the widths of all ancestors
  	while (i > 0) {
  		w += getTextWidth(nodeArray[i-1].name) + b.s;
  		i--;
  	}
    return "translate(" + (w) + ", 0)";
  });

  // Remove exiting nodes.
  g.exit().remove();

  // Now move and update the percentage at the end.
  d3.select("#trail").select("#endlabel")
      .attr("x", function() {
      	var totalLength = 0;
      	for (var i in nodeArray) {
      		totalLength += getTextWidth(nodeArray[i].name);
      	}      	
      	return 20 + totalLength; //(nodeArray.length + 0.5) * (b.w + b.s);
        })
      .attr("y", b.h / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", "left")
      .text(percentageString);

  // Make the breadcrumb trail visible, if it's hidden.
  d3.select("#trail")
      .style("visibility", "");

}




/**
 * Uses canvas.measureText to compute and return the width of the given text of given font in pixels.
 * 
 * @param {String} text The text to be rendered.
 * @param {String} font The css font descriptor that text is to be rendered with (e.g. "bold 14px verdana").
 * 
 * @see http://stackoverflow.com/questions/118241/calculate-text-width-with-javascript/21015393#21015393
 */
function getTextWidth(text, font) {
	if (!font) {font = "bold 12pt arial";}
    // re-use canvas object for better performance
    var canvas = getTextWidth.canvas || (getTextWidth.canvas = document.createElement("canvas"));
    var context = canvas.getContext("2d");
    context.font = font;
    var metrics = context.measureText(text);
    return metrics.width;
};



/* Helper function which adds an event listener to an object */
function addEvent(object, type, callback) {
    if (object == null || typeof(object) == 'undefined') return;
    if (object.addEventListener) {
        object.addEventListener(type, callback, false);
    } else if (object.attachEvent) {
        object.attachEvent("on" + type, callback);
    } else {
        object["on"+type] = callback;
    }
};

// Fires on window resize event. Position the svg circle 
// in the middle of its parent div
function resizeCircle() {
	var width = parseInt(d3.select("#d3_svg_container").style("width"), 10);
	var height = parseInt(d3.select("#d3_svg_container").style("height"), 10);	
	var scale_xy = computeScaling(document.getElementById("container"));
	var scale_str = "scale ( " + scale_xy + ", " + scale_xy + ")";
	d3.select("#container").
	attr("transform", "translate(" + width / 2 + "," + height / 2 + ") " + scale_str);	
}

addEvent(window, "resize", resizeCircle);

// check if an SVG <g> element has overflown relative to its parent svg
function computeScaling(el) {
   var parent = el.parentElement;
   var elBBox = el.getBBox();
   
   var x_scale = parent.width.animVal.value / elBBox.width;
   var y_scale = parent.height.animVal.value / elBBox.height;
   
   xy_scale = Math.min(x_scale, y_scale);
   var tolerance = 0.1;
   
   if (xy_scale < 1) {return 0.9*xy_scale;} // fix this, see TODO
   else if (xy_scale - tolerance > 1) {return xy_scale - tolerance;}
   else return 1.0;
}

