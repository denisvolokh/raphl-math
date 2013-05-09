function HomeController($http, $scope, $log, $rootScope) {
	$rootScope.root.showCalcPanel = false;

	$scope.uploading = false;

	$http.get("/listfiles")
		.success(function(data) {
			$scope.datasets = data.reverse();
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
		$scope.uploading = true;

		var formData = new FormData();
		if (angular.isDefined($scope.custom_name))
			formData.append("name", $scope.custom_name);
		if (angular.isDefined(uploadFile))
			formData.append("file", uploadFile);

		var xhr = new XMLHttpRequest;
		// xhr.addEventListener("load", function(e) {
		xhr.onreadystatechange = function(event) {
			if (event.currentTarget.readyState == 4 && event.currentTarget.status == 200) {
				$http.get("/listfiles")
					.success(function(data) {
						$scope.datasets = data.reverse();
				})	

				$scope.custom_name = "";
				$scope.uploading = false;	
			}
		};

		xhr.open('POST', '/upload', true);	
	    xhr.send(formData);
	}	

	$scope.removeFile = function(file) {
		$log.info(file);

		$http.get("/api/removefile?file_id="+file._id.$oid)
			.success(function(data) {
				$scope.datasets = data.reverse();
		})
	}
}