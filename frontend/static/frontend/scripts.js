/**
 *  Search is called whenever user clicks the search button. This finds any facet etc. on the screen and adds them as GET parameters.
 */
function search() {
	query = document.getElementById("query").value;
	//paramaters = find_site_parameters()
	var url = "search?query=" + query;
	window.location = url;
}


