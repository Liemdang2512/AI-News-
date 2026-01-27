const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

function log(message) {
  try {
    const logDir = app.getPath('userData');
    const logFile = path.join(logDir, 'app.log');
    const line = `[${new Date().toISOString()}] ${message}\n`;
    fs.appendFileSync(logFile, line);
  } catch {
    // Nếu ghi log lỗi thì bỏ qua, không làm app crash
  }
}

// Backend configuration must match backend/config.py
const BACKEND_HOST = '127.0.0.1';
const BACKEND_PORT = 8000;

let mainWindow = null;
let backendProcess = null;

function getBackendBinaryPath() {
  const resourcesPath = process.resourcesPath || __dirname;

  if (process.platform === 'darwin') {
    return path.join(resourcesPath, 'backend', 'mac', 'news-backend-mac');
  }

  if (process.platform === 'win32') {
    return path.join(resourcesPath, 'backend', 'win', 'news-backend-win.exe');
  }

  // For other platforms (e.g. dev on Linux), assume backend is already running
  return null;
}

function waitForBackendReady(timeoutMs = 15000) {
  const start = Date.now();

  return new Promise((resolve, reject) => {
    const check = () => {
      const req = http.request(
        {
          host: BACKEND_HOST,
          port: BACKEND_PORT,
          path: '/health',
          method: 'GET',
          timeout: 2000,
        },
        (res) => {
          if (res.statusCode === 200) {
            log('Backend healthcheck OK');
            resolve(true);
          } else if (Date.now() - start > timeoutMs) {
            reject(new Error('Backend healthcheck failed'));
          } else {
            setTimeout(check, 500);
          }
        },
      );

      req.on('error', () => {
        if (Date.now() - start > timeoutMs) {
          reject(new Error('Backend did not start in time'));
        } else {
          setTimeout(check, 500);
        }
      });

      req.end();
    };

    check();
  });
}

function startBackend() {
  const backendPath = getBackendBinaryPath();

  // If no binary path is resolved (e.g. dev on Linux), assume backend is already running
  if (!backendPath) {
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    log(`Starting backend from: ${backendPath}`);
    backendProcess = spawn(backendPath, [], {
      stdio: 'ignore',
      detached: process.platform === 'win32',
    });

    backendProcess.on('error', (err) => {
      log(`Backend process error: ${err.message}`);
      reject(err);
    });

    // Wait until /health returns OK
    waitForBackendReady()
      .then(() => {
        log('Backend started successfully');
        resolve();
      })
      .catch((err) => {
        log(`Backend failed to become ready: ${err.message}`);
        reject(err);
      });
  });
}

function stopBackend() {
  if (!backendProcess) return;

  try {
    if (process.platform === 'win32') {
      // On Windows, try to kill the process tree
      const { exec } = require('child_process');
      exec(`taskkill /pid ${backendProcess.pid} /T /F`);
    } else {
      backendProcess.kill('SIGTERM');
    }
  } catch (e) {
    log(`Error while stopping backend: ${e.message}`);
  } finally {
    log('Backend process reference cleared');
    backendProcess = null;
  }
}

function createMainWindow() {
  log('Creating main window');
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    show: false,
  });

  // Load static Next.js export
  // In production (packaged), files are in app.asar/frontend-dist
  // In development, files are in desktop/frontend-dist
  const indexPath = app.isPackaged
    ? path.join(__dirname, 'frontend-dist', 'index.html')
    : path.join(__dirname, 'frontend-dist', 'index.html');
  mainWindow.loadFile(indexPath);

  mainWindow.once('ready-to-show', () => {
    log('Main window ready to show');
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    log('Main window closed');
    mainWindow = null;
  });
}

async function bootstrap() {
  try {
    log('Bootstrap starting');
    await startBackend();
    createMainWindow();
  } catch (err) {
    log(`Bootstrap error: ${err.message}`);
    dialog.showErrorBox(
      'Backend error',
      `Không thể khởi động backend local.\n\nChi tiết: ${err.message}`,
    );
    app.quit();
  }
}

app.whenReady().then(() => {
  bootstrap();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      bootstrap();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    stopBackend();
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

