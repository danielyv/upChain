const {app, BrowserWindow, Menu, Tray, ipcMain, clipboard, globalShortcut} = require('electron')
const path = require('path')
const url = require('url')

// Gardez l'objet window dans une constante global, sinon la fenêtre sera fermée
// automatiquement quand l'objet JavaScript sera collecté par le ramasse-miettes.
let win
let contextMenu;
let appIcon;

function createWindow() {
    // Créer le browser window.
    win = new BrowserWindow({width: 1045, height: 600, icon: './img/icon.ico', show: false, frame: false})

    // et charge le index.html de l'application.
    win.loadURL(url.format({
        pathname: path.join(__dirname, 'index.html'),
        protocol: 'file:',
        slashes: true
    }))
    appIcon = new Tray(path.join(__dirname, './img/icon.ico'));

    // Ouvre le DevTools.
    // Émit lorsque la fenêtre est fermée.
    win.on('close', function (event) {
        if (!app.isQuiting) {
            event.preventDefault();
            win.hide();
        }

        return false;
    });
    win.on('minimize', function (event) {
        event.preventDefault();
        win.hide();
    });
    contextMenu = Menu.buildFromTemplate([
        {
            label: 'Show App', click: function () {
                win.show();
            }
        },
        {
            label: 'Quit', click: function () {
                app.isQuiting = true;
                app.quit();
            }
        }
    ]);
    appIcon.setToolTip('upChain');
    appIcon.setContextMenu(contextMenu);
}

// Cette méthode sera appelée quant Electron aura fini
// de s'initialiser et sera prêt à créer des fenêtres de navigation.
// Certaines APIs peuvent être utilisées uniquement quant cet événement est émit.
app.on('ready', () => {
    createWindow()
    globalShortcut.register('Ctrl+Q', () => {
        if(win.isVisible()){
            win.hide()
        }else{
            win.show()
        }
    })
})
// Quitte l'application quand toutes les fenêtres sont fermées.
app.on('window-all-closed', () => {
    // Sur macOS, il est commun pour une application et leur barre de menu
    // de rester active tant que l'utilisateur ne quitte pas explicitement avec Cmd + Q
    if (process.platform !== 'darwin') {
        app.quit()
    }
})

app.on('activate', () => {
    // Sur macOS, il est commun de re-créer une fenêtre de l'application quand
    // l'icône du dock est cliquée et qu'il n'y a pas d'autres fenêtres d'ouvertes.
    if (win === null) {
        createWindow()

    }
})
ipcMain.on("sendImageR", (event, args) => {
    var request = require('request');
    var fs = require('fs');
    var url = "http:\/\/guiltycore.fr:5000\/mine_block"
    var x = fs.createReadStream(args)

    var req = request.post(url, function (err, resp, body) {
        if (!err) {
            event.sender.send('sendImageM', body);

        }
    });
    var form = req.form();
    form.append('file', x);

});

ipcMain.on('loadHistoricR', (event) => {

    var request = require('request');
    request.get('http://guiltycore.fr:5000/blockchain_historic', function (error, response, body) {
        event.sender.send('loadHistoricM', body);
    });
});
ipcMain.on('clipboardR', (event, args) => {
    clipboard.writeText(args)

});
ipcMain.on('exit', (event) => win.hide())

