// Create our own local controller service.
// We have namespaced local services with "hello:"
var helloControllerService = SYMPHONY.services.register("hello:controller");

// This is the message controller service, to be used for static and dynamic rendering
var messageControllerService = SYMPHONY.services.register("message:controller");

// All Symphony services are namespaced with SYMPHONY
SYMPHONY.remote.hello().then(function(data) {

    // Register our application with the Symphony client:
    // Subscribe the application to remote (i.e. Symphony's) services
    // Register our own local services
    SYMPHONY.application.register("hello", ["modules", "applications-nav", "ui", "share", "entity"], ["hello:controller", "message:controller"]).then(function(response) {

        // The userReferenceId is an anonymized random string that can be used for uniquely identifying users.
        // The userReferenceId persists until the application is uninstalled by the user. 
        // If the application is reinstalled, the userReferenceId will change.
        var userId = response.userReferenceId;

        // Subscribe to Symphony's services
        var modulesService = SYMPHONY.services.subscribe("modules");
        var navService = SYMPHONY.services.subscribe("applications-nav");

        var entityService = SYMPHONY.services.subscribe("entity");
        entityService.registerRenderer(
            "com.symphony.hackathon.bitweaver",
            {},
            "message:controller"
        );

        // LEFT NAV: Add an entry to the left navigation for our application
        navService.add("hello-nav", "Hello World App", "hello:controller");

        // Implement some methods on our local service. These will be invoked by user actions.
        helloControllerService.implement({

            // LEFT NAV & MODULE: When the left navigation item is clicked on, invoke Symphony's module service to show our application in the grid
            select: function(id) {
                if (id == "hello-nav") {
                    // Focus the left navigation item when clicked
                    navService.focus("hello-nav");
                }

                modulesService.show("hello", {title: "Hello World App"}, "hello:controller", "https://localhost:4000/app.html", {
                    // You must specify canFloat in the module options so that the module can be pinned
                    "canFloat": true,
                });
                // Focus the module after it is shown
                modulesService.focus("hello");
            }
        });


        // Implement some methods to render the structured objects sent by the app to our specified thread
        messageControllerService.implement({

            // Use the entity data to update the rendering of the message through the entity service
            rerender: function(tracked) {
                var entityData = tracked.entityData;
                return entityService.update(entityData.entityInstanceId, entityData.template, entityData.data);
            },

            // Render the message sent by the app
            render: function(type, entityData) {

                console.log(entityData)
                var fromUserId = entityData.fromUserId
                var question = entityData.question

                if (type == "com.symphony.hackathon.bitweaver") {
                    return {
                      template: '<messageML><iframe src="https://localhost:8092/who/'+fromUserId+'?question='+question+'" height="120px"/></messageML>',
                      data: {}
                    };
                }
            }
        });
    }.bind(this))
}.bind(this));