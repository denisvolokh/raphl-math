function CalcController($log, $scope, $rootScope, $routeParams, $http) {
	$http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";
	$scope.position = 1;
	$rootScope.root.loading = true;
	$rootScope.root.showCalcPanel = true;

	$scope.listRecords = function() {
		if (angular.isDefined($routeParams["id"])) {
			$rootScope.root.loading = true;
			$http.get("/listrecords?dataset_id=" + $routeParams["id"])
				.success(function(data) {
					$scope.records = data.result;
					$rootScope.root.selectedFile = data.file.name;
					$rootScope.root.loading = false;
				})
		}	
	}

	$rootScope.reCalculate = function() {
		if (angular.isDefined($routeParams["id"])) {
			$rootScope.root.loading = true;
			$log.info($scope.position);
			var pos = Number($scope.position) * 1000000;
			$http.get("/api/calc?dataset_id=" + $routeParams["id"] + "&position=" + pos)
				.success(function(data) {
					$scope.records = data.result;
					$rootScope.root.selectedFile = data.file.name;
					$rootScope.root.loading = false;
				})
		}	
	}

	$scope.getRecordClass = function(item) {
		return item.highlight
	}

	$scope.listRecords();
}