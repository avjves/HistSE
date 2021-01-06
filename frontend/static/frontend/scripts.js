/*
 * Adds / removes a facet selection. Works by adding the selection to the siteParameters directly
 * and then calling search without any new values.
 */
function setNewFacet(facetKey, facetValue) {
	//const currentFacets = siteParameters.fq != undefined ? siteParameters.fq.split(",") : [];
	const currentFacets = siteParameters.fq != undefined ? siteParameters.fq: [];
	const newFacets = [];
	var facetFound = false;
	for(var i = 0; i < currentFacets.length; i++) {
		splits = currentFacets[i].split(":");
		currentFacetKey = splits[0];
		currentFacetValue = splits[1];
		if(currentFacetKey == facetKey) {
			facetFound = true;
			if(facetValue == '') { // No value means that we want to remove a facet instead of adding a new one
				continue;
			}
			else {
				newFacets.push(currentFacetKey + ':' + currentFacetValue);
			}
		}
		else {
			newFacets.push(currentFacetKey + ':' + currentFacetValue);
		}
	}
	if(!facetFound) {
		newFacets.push(facetKey + ':' + facetValue); 
	}
	siteParameters.fq = newFacets;
	console.log(siteParameters.fq)
	search();
}


/**
 * Uses the site parameters and adds a new value to them, if one exists.
 */
function find_site_parameters(newOption, newValue) {
	parameters = siteParameters; // These are returned by default by Django template
	if(newOption != null) {
		parameters[newOption] = newValue;	
	}
	return parameters;
}

/*
 * Generates a new URL to fetch given the parameters.
 */
function generate_new_url(parameters) {
	params = [];
	for (const key in parameters) {
		if(jsonKeys.includes(key)) {
			console.log("KEY")
			console.log(key)
			params.push(key + "=" + JSON.stringify(parameters[key]));
		}
		else {
			params.push(key + "=" + parameters[key]);
		}
	}
	console.log(params);
	const url = "search?" + params.join("&");
	return url;
}

/**
 *  Search is called whenever user clicks the search button. This finds any facet etc. on the screen and adds them as GET parameters.
 */
function search(newOption=null, newValue=null) {
	paramaters = find_site_parameters(newOption, newValue)
	new_url = generate_new_url(parameters);
	//var url = "search?q=" + query;
	window.location = new_url;
}


jsonKeys = ['fq']
