const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 450,
    height: 120,
    frame: false,           // Removes the OS window border/controls
    transparent: true,      // Allows CSS background: transparent to work
    alwaysOnTop: true,      // Floats above VS Code, Chrome, etc.
    resizable: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  win.loadFile('index.html');
}

// Some systems require hardware acceleration to be disabled for true transparency
app.disableHardwareAcceleration();

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});