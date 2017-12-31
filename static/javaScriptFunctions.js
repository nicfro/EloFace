function sendVoteData(choice) {
	var data 
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
	var data 
	var info = {}

	info.username = username.value
	info.password = password.value
	info.country = country.value
	info.email = email.value
	info.gender = gender.value
	info.bday = bday.value 

	$.ajax({
	  type: "POST",
	  url: "/createNewUser",
	  data: info,
	  dataType: "json",
	  success: function(data) {
      writewarning(data); 
    }
	});
}

function sendLogin() {
	var data 
	var info = {}

	info.username = username.value
	info.password = password.value

	$.ajax({
	  type: "POST",
	  url: "/login",
	  data: info,
	  dataType: "json",
	  success: function(response, status, xhr){ 
	    var ct = xhr.getResponseHeader("content-type") || "";
	    console.log(xhr.getResponseHeader("content-type"))
	    if (ct.indexOf('text/html; charset=utf-8') > -1) {
	   	  console.log("KOM NU")
	      window.location.href = "http://stackoverflow.com";
	    }
	    if (ct.indexOf('json') > -1) {
	      console.log("xdxd")
      	  writewarning(response);
	  	}
      }
	});
}

function writewarning(errors){
	$('#warning').html("")
	for (var key in errors) {
		if (errors.hasOwnProperty(key)) {
			$('#warning').append("<p>")
			$('#warning').append(errors[key])
			$('#warning').append("</p>")
			$('#warning').append("</br>")
		}
	}
}

