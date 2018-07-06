// Create our own local service pertaining to the application module
// We have namespaced local services with "hello:"
var helloAppService = SYMPHONY.services.register("hello:app");


var $ = require('jquery');

SYMPHONY.remote.hello().then(function(data) {

    // Set the theme of the app module
    var themeColor = data.themeV2.name;
    var themeSize = data.themeV2.size;
    // You must add the symphony-external-app class to the body element
    document.body.className = "symphony-external-app " + themeColor + " " + themeSize;

    SYMPHONY.application.connect("hello", ["modules"], ["hello:app"]).then(function(response) {

        // The userReferenceId is an anonymized random string that can be used for uniquely identifying users.
        // The userReferenceId persists until the application is uninstalled by the user. 
        // If the application is reinstalled, the userReferenceId will change.
        var userId = response.userReferenceId;
        
    }.bind(this))
}.bind(this));
