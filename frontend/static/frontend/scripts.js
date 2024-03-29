function search() {
	var q = document.getElementById("query").value;
	q = q.replaceAll("+", "%2b")
	const currentUrl = window.location.href;
	const getParams = window.location.search.substr(1)
	const splitParams = getParams.split("&");
	var qfound = false;
	var newParams = [];
	for(var i = 0; i < splitParams.length; i++) {
		key = splitParams[i].split("=")[0]
		if(key.length == 0) {
			continue;
		}
		console.log(key);
		value = splitParams[i].substring(key.length + 1)
		if(key == "q") {
			value = q;
			qfound = true;
		}
		if(key == 'fq') {
			continue;
		}
		newParams.push(key + "=" + value);
	}
	if(!qfound) {
		newParams.push("q=" + q);
	}
	console.log(currentUrl)
	console.log(getParams)
	console.log(newParams)
	var newUrl = '';
	if(getParams.length == 0) {
		var handler = currentUrl.split("/");
		handler = handler[handler.length-1];
		var okHandles = ['search', 'charts', 'year', 'month'];
		if(okHandles.includes(handler)) {
			handler = '';
		}
		else {
			handler = 'hits/search';
		}
		newUrl = currentUrl + handler + "?" + newParams.join("&");	
		console.log(newUrl);
	}
	else {
		newUrl = currentUrl.replace(getParams, newParams.join("&")).replace("/cluster/", "/hits/");
	}
	console.log(newUrl);
	window.location = newUrl;
}


function showInfo() {
	document.getElementById("helpOverlay").style.display = "block";
}

function hideInfo() {
	document.getElementById("helpOverlay").style.display = "none";
}
