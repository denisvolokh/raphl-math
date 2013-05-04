function HomeController($http, $scope, $log) {


	$http.get("/listfiles")
		.success(function(data) {
			$scope.datasets = data;
		})

	$scope.readyToUpload = true;
	var uploadFile;

	$scope.setFile = function(element) {
		uploadFile = element.files[0];
		if (uploadFile) {
			$scope.readyToUpload = true;
		}
	};	
		
	$scope.submitFile = function() {
		var formData = new FormData();
		if (angular.isDefined($scope.custom_name))
			formData.append("name", $scope.custom_name);
		if (angular.isDefined(uploadFile))
			formData.append("file", uploadFile);

		var xhr = new XMLHttpRequest;
		xhr.onreadystatechange = function(event) {
			$http.get("/listfiles")
				.success(function(data) {
				$scope.datasets = data;
			})
				$scope.custom_name = "";
		};

		xhr.open('POST', '/upload', true);	
	    xhr.send(formData);
	}	
}