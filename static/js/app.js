var app = angular.module("app", ['ngResource', "$strap.directives"]);

app.config(function($interpolateProvider) {
	$interpolateProvider.startSymbol('{[{');
  	$interpolateProvider.endSymbol('}]}');
});

app.config(function($routeProvider) {
	$routeProvider.when("/", {
		templateUrl: "static/partials/home.html",
		controller: "HomeController"
	}).when("/calc/:id", {
		templateUrl: "static/partials/calc.html?12312312",
		controller: "CalcController" 
	}).otherwise({
		redirectTo: "/"
	});
});

app.run(function($rootScope, $location, $http, $log) {
	$log.info("[+] App is running!")
	
	$rootScope.root = {
		showCalcPanel: false,
		loading: false,
		selectedFile: "",
		position: 1000000,
		strategy: 1
	}
});
