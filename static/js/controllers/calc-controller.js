function CalcController($log, $scope, $rootScope, $routeParams, $http) {
	$http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";
	$scope.position = 1;
	$rootScope.root.loading = true;
	$rootScope.root.showCalcPanel = true;
	$scope.page = 1
	$scope.pages = 0;
	$scope.records = [];
	$scope.calc_hash = "";

	$scope.listRecords = function() {
		if (angular.isDefined($routeParams["id"])) {
			$rootScope.root.loading = true;
			$http.get("/listrecords?dataset_id=" + $routeParams["id"] + "&page=" + $scope.page + "&calc_hash=" + $scope.calc_hash)
				.success(function(data) {
					$rootScope.root.selectedFile = data.file.name;
					$rootScope.root.loading = false;

					if ($scope.records.length > 0) {
						angular.forEach(data.result, function(item) {
							$scope.records.push(item);	
						})
					} else {
						$scope.records = data.result;
					}
					// $log.info("[+]", $scope.records)
					$scope.pages = data.pages;
				})
		}	
	}

	$rootScope.reCalculate = function() {
		if (angular.isDefined($routeParams["id"])) {
			$rootScope.root.loading = true;
			$log.info($scope.position);
			$scope.page = 1;
			var pos = Number($rootScope.root.position);
			$http.get("/api/calc?dataset_id=" + $routeParams["id"] + 
					"&position=" + pos + 
					"&page=" + $scope.page + 
					"&calc_hash=" + $scope.calc_hash + 
					"&strategy=" + $rootScope.root.strategy)
				.success(function(data) {
					$scope.pages = data.pages;
					$scope.trades_counter = data.trades_counter;
					$scope.min = data.min;
					$scope.max = data.max;
					$scope.sum_profit_bp = data.sum_profit_bp;
					$scope.sum_profit_loss = data.sum_profit_loss;
					$rootScope.root.selectedFile = data.file.name;
					$rootScope.root.loading = false;

					$scope.calc_hash = data.calc_hash;	
					$scope.records = data.result;
				})
		}	
	}

	$scope.loadMore = function() {
		$scope.page += 1;

		$scope.listRecords();	 
	}

	$rootScope.doExportData = function() {
		if (angular.isDefined($routeParams["id"])) {
			var pos = Number($rootScope.root.position);
			$.fileDownload("/api/export?dataset_id=" + $routeParams["id"] + "&position=" + pos);
		}	
	}

	$scope.getRecordClass = function(item) {
		return item.highlight
	}

	$scope.listRecords();
}