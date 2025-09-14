/**
 * Node-RED Settings for Orchestrator Platform
 * 
 * This configuration file sets up Node-RED for the robotics orchestrator
 * with MQTT integration and dashboard capabilities.
 */

module.exports = {
    // The tcp port that the Node-RED web server is listening on
    uiPort: process.env.PORT || 1880,

    // By default, the Node-RED UI accepts connections on all IPv4 interfaces.
    // To only allow connections from localhost, uncomment the following property.
    // uiHost: "127.0.0.1",

    // Retry time in milliseconds for MQTT connections
    mqttReconnectTime: 15000,

    // Timeout in milliseconds for TCP server socket connections
    // defaults to no timeout
    // socketTimeout: 120000,

    // Maximum number of messages to wait in queue while disconnected
    // defaults to 1000
    // socketReconnectTime: 15000,

    // The maximum length, in characters, of any message sent to the debug sidebar tab
    debugMaxLength: 1000,

    // The file containing the flows. If not set, it defaults to flows_<hostname>.json
    flowFile: 'flows.json',

    // To enabled pretty-printing of the flow within the flow file, set the following
    // property to true:
    flowFilePretty: true,

    // By default, credentials are encrypted in storage using a generated key. To
    // specify your own secret, set the following property.
    // If you want to disable encryption of credentials, set this property to false.
    // Note: once you set this property, do not change it - doing so will prevent
    // node-red from being able to decrypt your existing credentials and they will be
    // lost.
    credentialSecret: "orchestrator-platform-secret",

    // By default, all user data is stored in a directory called `.node-red` under
    // the user's home directory. To use a different location, the following
    // property can be used
    userDir: './configs/node_red_config/',

    // Node-RED scans the `nodes` directory in the userDir to find local node files.
    // The following property can be used to specify an additional directory to scan.
    nodesDir: './configs/node_red_config/nodes/',

    // By default, the Node-RED UI is available at http://localhost:1880/
    // The following property can be used to specify a different root path.
    // If set to false, this is disabled.
    httpRoot: '/',

    // The following property can be used to specify a different root path for
    // the admin interface. If not set, it defaults to httpRoot + 'admin'.
    // If set to false, this is disabled.
    httpAdminRoot: '/admin',

    // Some nodes, such as HTTP In, can be used to listen for incoming http requests.
    // By default, these are served relative to '/'. The following property
    // can be used to specifiy a different root path. If set to false, this is
    // disabled.
    httpNodeRoot: '/api',

    // The following property can be used to add a custom middleware function
    // in front of the HTTP In node.
    // httpNodeMiddleware: function(req,res,next) {
    //    // Handle/reject the request, or pass it on to the HTTP In node by calling next();
    //    // Optionally skip our rawBodyParser by setting this to true;
    //    req.skipRawBodyParser = true;
    //    next();
    // },

    // When httpAdminRoot is used to move the UI to a different root path, the
    // following property can be used to identify a directory of static content
    // that should be served at http://localhost:1880/.
    httpStatic: './configs/node_red_config/public/',

    // The maximum size of HTTP request that will be accepted by the runtime api.
    // Default: 5mb
    apiMaxLength: '5mb',

    // If you installed the optional node-red-dashboard you can set it's path
    // relative to httpRoot
    ui: { path: "ui" },

    // Securing Node-RED
    // -----------------
    // To password protect the Node-RED editor and admin API, the following
    // property can be used. See http://nodered.org/docs/security.html for details.
    adminAuth: {
        type: "credentials",
        users: [{
            username: "admin",
            password: "$2a$08$zZWtXTja0fB1pzD4sHCMyOCMYz2Z6dNbM6tl8sJogENOMcxWV9DN.",
            permissions: "*"
        }]
    },

    // To password protect the node-defined HTTP endpoints (httpNodeRoot), or
    // the static content (httpStatic), the following properties can be used.
    // The pass phrase in the default settings is 'node-red'.
    httpNodeAuth: {user:"node",pass:"$2a$08$zZWtXTja0fB1pzD4sHCMyOCMYz2Z6dNbM6tl8sJogENOMcxWV9DN."},
    httpStaticAuth: {user:"node",pass:"$2a$08$zZWtXTja0fB1pzD4sHCMyOCMYz2Z6dNbM6tl8sJogENOMcxWV9DN."},

    // The following property can be used to enable HTTPS
    // See http://nodejs.org/api/https.html#https_https_createserver_options_requestlistener
    // for details on its contents.
    // See the comment at the top of this file on how to load the `fs` module used by
    // this setting.
    //
    //https: {
    //    key: fs.readFileSync('privatekey.pem'),
    //    cert: fs.readFileSync('certificate.pem')
    //},

    // The following property can be used to refresh the context store
    // at a regular interval (in seconds)
    // contextStorage: {
    //    default: "memoryOnly",
    //    memoryOnly: { module: 'memory' },
    //    file: { module: 'localfilesystem' }
    // },

    // The following property can be used to order the categories in the editor
    // palette. If a node's category is not in the list, the category will get
    // added to the end of the palette.
    // If not set, the following default order is used:
    paletteCategories: ['subflows', 'common', 'function', 'network', 'sequence', 'parser', 'storage'],

    // Configure the logging output
    logging: {
        // Only console logging is currently supported
        console: {
            // Level of logging to be recorded. Options are:
            // fatal, error, warn, info, debug, trace
            level: "info",
            // Whether or not to include metric events in the log output
            metrics: false,
            // Whether or not to include audit events in the log output
            audit: false
        }
    },

    // Customising the editor
    editorTheme: {
        projects: {
            // To enable the Projects feature, set this value to true
            enabled: false
        },
        palette: {
            // Enable/disable the Palette Manager
            editable: true,
            // Configure the categories displayed in the palette
            categories: ['subflows', 'common', 'function', 'network', 'sequence', 'parser', 'storage']
        },
        menu: {
            // Hide unwanted menu items by id. see packages/node_modules/@node-red/editor-client/src/js/red.js:loadEditor for complete list
            "menu-item-import-library": false,
            "menu-item-export-library": false,
            "menu-item-keyboard-shortcuts": false,
            "menu-item-help": {
                label: "Node-RED website",
                url: "http://nodered.org"
            }
        }
    },

    // Allow the Function node to load additional npm modules directly
    functionExternalModules: true,

    // The following property can be used to set predefined values in Global Context.
    // This allows extra node modules to be made available with the Function node.
    // For example, the following:
    //    functionGlobalContext: { os:require('os') }
    // will allow the `os` module to be accessed in a Function node using:
    //    global.get("os")
    functionGlobalContext: {
        // os:require('os'),
        // jfive:require("johnny-five"),
        // j5board:require("johnny-five").Board({repl:false})
    },

    // `global.keys()` returns a list of all properties set in global context.
    // This allows them to be displayed in the Context Sidebar within the editor.
    // In some circumstances it is not desirable to expose them to the editor. The
    // following property can be used to hide any property set in `functionGlobalContext`
    // from being list by `global.keys()`.
    // By default, the property is set to false to avoid accidental exposure of
    // their values. Setting this to true will cause the keys to be listed.
    exportGlobalContextKeys: false,

    // Configure how the runtime will handle external npm modules.
    // This covers:
    //  - whether the editor will allow new node modules to be installed
    //  - whether nodes, such as the Function node are allowed to have their
    // own dynamically configured dependencies.
    // The allow/denyList options can be used to limit what modules the runtime
    // will install or load. It can use '*' as a wildcard that matches anything.
    externalModules: {
        // autoInstall: false,   // Whether the runtime will attempt to automatically install missing modules
        // autoInstallRetry: 30, // Interval, in seconds, between reinstall attempts
        // palette: {              // Configuration for the Palette Manager
        //     allowInstall: true, // Enable the Palette Manager in the editor
        //     allowUpdate: true,  // Allow modules to be updated in the editor
        //     allowUpload: true,  // Allow module tgz files to be uploaded and installed
        //     allowList: ['*'],
        //     denyList: [],
        //     allowUpdateList: ['*'],
        //     denyUpdateList: []
        // },
        // modules: {              // Configuration for node-specified modules
        //     allowInstall: true,
        //     allowList: ['*'],
        //     denyList: []
        // }
    }
};