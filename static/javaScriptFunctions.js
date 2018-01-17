function sendVoteData(choice) {
	var choice
	var info = {}

	var pic1 = $('#image1').attr('src')
	var pic2 = $('#image2').attr('src')

	info.choice = choice
	info.pic1 = pic1
	info.pic2 = pic2

	$.ajax({
	  type: "POST",
	  url: "/vote",
	  data: info,
	  dataType: "json",
	  success: location.reload()
	});
}

function sendCreateNewUserData() {
	var info = {}

	info.username = username.value
	info.password = password.value
	info.country = country.value
	info.email = email.value
	info.gender = gender.value
	info.bday = bday.value 
	info.race = race.value

	$.ajax({
	  type: "POST",
	  url: "/createNewUser",
	  data: info,
	  success: function(response, status, xhr){
	    var ct = xhr.getResponseHeader("content-type") || "";
	    if (ct.indexOf('text/html') > -1) {
	      window.location.href = "/";
	    }
	    if (ct.indexOf('json') > -1) {
      	  writewarning(response);
	  	}
      }
	});
}

function sendLogin(datatype) {
	var info = {}

	info.username = username.value
	info.password = password.value

	$.ajax({
	  type: "POST",
	  url: "/login",
	  data: info,
	  success: function(response, status, xhr){
	    var ct = xhr.getResponseHeader("content-type") || "";
	    if (ct.indexOf('text/html') > -1) {
	    //fix so it loads response instead of redirects
	      window.location.href = "/";
	    }
	    if (ct.indexOf('json') > -1) {
      	  writewarning(response);
	  	}
      }
	});
}

function sendImage(imageData) {
	var info = {}

	info.upload = imageData
	info.gender = gender.value
	info.race = race.value
	info.ageGroup = ageGroup.value
	
	$.ajax({
	  type: "POST",
	  url: "/uploadToS3",
	  data: info,
	  enctype: 'multipart/form-data',
	  dataType: "json",

	  success: function(response, status, xhr){
	    var ct = xhr.getResponseHeader("content-type") || "";
	    if (ct.indexOf('text/html') > -1) {
	    //fix so it loads response instead of redirects
	      window.location.href = "/";
	    }
	    if (ct.indexOf('json') > -1) {
      	  writewarning(response);
	  	}
      }
	});
}
function writewarning(errors){
	$('.warningFields').empty()
	for (var key in errors) {
		if (errors.hasOwnProperty(key)) {
			$('#'+key).html("<p>"+errors[key]+"</p>")
		}
	}
}