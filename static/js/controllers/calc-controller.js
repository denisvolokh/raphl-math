function CalcController($log, $scope, $routeParams, $http) {
	$http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";
	$scope.position = 1;

	$scope.listRecords = function() {
		if (angular.isDefined($routeParams["id"])) {
			$http.get("/listrecords?dataset_id=" + $routeParams["id"])
				.success(function(data) {
					$scope.records = data.result;
					$scope.filename = data.file.name;
				})
		}	
	}

	$scope.reCalculate = function() {
		if (angular.isDefined($routeParams["id"])) {
			$log.info($scope.position);
			var pos = Number($scope.position) * 1000000;
			$http.get("/api/calc?dataset_id=" + $routeParams["id"] + "&position=" + pos)
				.success(function(data) {
					$scope.records = data.result;
					$scope.filename = data.file.name;
				})
		}	
	}

	$scope.getRecordClass = function(item) {
		return item.highlight
	}

	$scope.listRecords();
}