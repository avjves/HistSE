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
	parameters = {};
	parameters.q = document.getElementById("query").value;

	// Adding the just added new option
	if(newOption != null) {
		parameters[newOption] = newValue;	
	}
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
