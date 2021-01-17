function searchq() {
	const q = document.getElementById("query").value;
	const currentUrl = window.location.href;
	const getParams = window.location.search.substr(1)
	const splitParams = getParams.split("&");
	var newParams = [];
	for(var i = 0; i < splitParams.length; i++) {
		key = splitParams[i].split("=")[0]
		console.log(key);
		value = splitParams[i].substring(key.length + 1)
		if(key == "q") {
			value = q;
		}
		if(key == 'fq') {
			continue;
		}
		newParams.push(key + "=" + value);

	}
	window.location = currentUrl.replace(getParams, newParams.join("&"));
}

