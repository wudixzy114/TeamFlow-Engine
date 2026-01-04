import {app, shell, BrowserWindow, ipcMain} from 'electron'
import {join} from 'path'
import {electronApp, optimizer, is} from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import {setupP2PIPC, cleanupP2P} from "./p2p/ipc";
import {setupAiIPC} from "./ai/ipc";

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    frame: false,
    titleBarStyle: 'hidden',
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? {icon} : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.on('maximize', () => {
    mainWindow.webContents.send('window-state-change', 'maximized')
  })

  mainWindow.on('unmaximize', () => {
    mainWindow.webContents.send('window-state-change', 'normal')
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return {action: 'deny'}
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  console.log('[Main] Registering P2P IPC...')
  try {
    setupP2PIPC(mainWindow) // <--- 尝试包裹 try-catch 看看报什么错
  } catch (e) {
    console.error('CRITICAL ERROR in setupP2PIPC:', e)
  }
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.electron')

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // IPC test
  ipcMain.on('ping', () => console.log('pong'))

  try {
    setupAiIPC() // <--- 尝试包裹 try-catch 看看报什么错
  } catch (e) {
    console.error('CRITICAL ERROR in setupAiIPC:', e)
  }

  createWindow()

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('before-quit', () => {
  cleanupP2P();
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

ipcMain.on('window-minimize', (event) => {
  const webContents = event.sender
  const win = BrowserWindow.fromWebContents(webContents)
  if (win) win.minimize()
})

ipcMain.on('window-maximize', (event) => {
  const webContents = event.sender
  const win = BrowserWindow.fromWebContents(webContents)
  if (win) {
    if (win.isMaximized()) {
      win.unmaximize()
    } else {
      win.maximize()
    }
  }
})

ipcMain.on('window-close', (event) => {
  const webContents = event.sender
  const win = BrowserWindow.fromWebContents(webContents)
  if (win) win.close()
})

ipcMain.handle('window-is-maximized', (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  return win ? win.isMaximized() : false
})
