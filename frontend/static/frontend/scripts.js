/**
 *  Search is called whenever user clicks the search button. This finds any facet etc. on the screen and adds them as GET parameters.
 */
function search(newOption=null, newValue=null) {
	paramaters = find_site_parameters(newOption, newValue)
	new_url = generate_new_url(parameters);
	//var url = "search?q=" + query;
	window.location = new_url;
}

function find_site_parameters(newOption, newValue) {
	parameters = siteParameters;
	//parameters = {};
	//const currentLocation = window.location.href;
	//console.log(window.location.search);
	//return parameters
	//const params = currentLocation.split("?", 2)[1].split("&");
	//for(var i = 0; i < params.length; i++) {
		//key = params[i].split("=", 1);
		//parameters[key] = params[i].substring(key.length, params[i].length); 
	//}
	//console.log(parameters);
	console.log(newOption, newValue)
	if(newOption != null) {
		parameters[newOption] = newValue;	
	}
	console.log(parameters);
	return parameters;

}


function generate_new_url(parameters) {
	params = [];
	for (const key in parameters) {
		params.push(key + "=" + parameters[key]);
	}
	const url = "search?" + params.join("&");
	return url;
}
