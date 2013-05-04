function CalcController($log, $scope, $routeParams, $http) {
	$http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";

	if (angular.isDefined($routeParams["id"])) {
		$http.get("/listrecords?dataset_id=" + $routeParams["id"])
			.success(function(data) {
				$scope.records = data;
			})
	}

	$scope.getRecordClass = function(item) {
		if (item.highlight == true)
			return "success"

		return ""
	}
}