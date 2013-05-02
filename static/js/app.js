var app = angular.module("app", ['ngResource']);

app.config(function($routeProvider) {
	$routeProvider.when("/", {
		templateUrl: "static/partials/home.html",
		controller: "HomeController"
	}).when("/calc", {
		templateUrl: "static/partials/calc.html?12312312",
		controller: "CalcController" 
	}).otherwise({
		redirectTo: "/"
	});
});

app.run(function($rootScope, $location, $http, $log) {
	$log.info("[+] App is running!")
	$rootScope.root = {
        
    };

	// $http.get(user_api + "/islogged")
	// 	.success(function(data) {
	// 		$rootScope.root.isUserLogged = data.status;
	// 		if (data.status == true) {
	// 			$rootScope.root.user = data.result;		
	// 		}
	// 		$location.path("/home");
	// 	})
	// 	.error(function(data) {
	// 		$log.warn("[-] Error on /islogged");
	// 	});
	
});
