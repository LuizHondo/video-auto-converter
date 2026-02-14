const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const Store = require('electron-store')
const os = require('os')

const store = new Store()

let mainWindow = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 700,
    backgroundColor: '#0f1419',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    show: false,
  })

  // Load the app
  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// IPC Handlers
ipcMain.handle('select-folder', async () => {
  const lastExportDir = store.get('lastExportDir')
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory'],
    defaultPath: lastExportDir || undefined,
  })
  if (!result.canceled && result.filePaths.length > 0) {
    const selectedPath = result.filePaths[0]
    store.set('lastExportDir', selectedPath)
    return selectedPath
  }
  return null
})

ipcMain.handle('select-videos', async () => {
  const lastImportDir = store.get('lastImportDir')
  const result = await dialog.showOpenDialog({
    properties: ['openFile', 'multiSelections'],
    defaultPath: lastImportDir || undefined,
    filters: [
      { name: 'Videos', extensions: ['mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm'] },
      { name: 'All Files', extensions: ['*'] },
    ],
  })
  if (!result.canceled && result.filePaths.length > 0) {
    // Remember the folder where videos were selected from
    const firstFile = result.filePaths[0]
    const folderPath = path.dirname(firstFile)
    store.set('lastImportDir', folderPath)
    return result.filePaths
  }
  return []
})

ipcMain.handle('get-setting', async (_, key) => {
  return store.get(key)
})

ipcMain.handle('set-setting', async (_, key, value) => {
  store.set(key, value)
  return true
})

// Find Python command
function findPythonCommand() {
  return new Promise((resolve, reject) => {
    const commands = ['python', 'python3', 'py']
    let index = 0

    const tryNext = () => {
      if (index >= commands.length) {
        reject(new Error('Python not found. Please install Python and make sure it\'s in your PATH.'))
        return
      }

      const cmd = commands[index]
      const test = spawn(cmd, ['--version'])

      test.on('error', () => {
        index++
        tryNext()
      })

      test.on('close', (code) => {
        if (code === 0) {
          console.log(`Found Python: ${cmd}`)
          resolve(cmd)
        } else {
          index++
          tryNext()
        }
      })
    }

    tryNext()
  })
}

ipcMain.handle('process-video', async (_, args) => {
  let pythonCmd
  try {
    pythonCmd = await findPythonCommand()
  } catch (error) {
    return { success: false, error: error.message }
  }

  const pythonScript = process.env.VITE_DEV_SERVER_URL
    ? path.join(process.cwd(), 'python', 'processor.py')
    : path.join(process.resourcesPath, 'python', 'processor.py')

  console.log('Processing video:', args.inputPath)
  console.log('Python command:', pythonCmd)
  console.log('Python script:', pythonScript)

  return new Promise((resolve, reject) => {
    const python = spawn(pythonCmd, [
      pythonScript,
      args.inputPath,
      args.outputPath,
      args.caption || '',
      args.font || 'Impact',
    ], {
      // Don't create a window on Windows
      windowsHide: true,
    })

    let stdout = ''
    let stderr = ''

    python.stdout.on('data', (data) => {
      const chunk = data.toString()
      console.log('Python stdout:', chunk)
      stdout += chunk
      const lines = chunk.split('\n')
      for (const line of lines) {
        if (line.includes('PROGRESS:')) {
          const match = line.match(/PROGRESS: ([\d.]+)/)
          if (match && mainWindow) {
            mainWindow.webContents.send('processing-progress', {
              path: args.inputPath,
              progress: parseFloat(match[1]),
            })
          }
        }
      }
    })

    python.stderr.on('data', (data) => {
      const chunk = data.toString()
      console.error('Python stderr:', chunk)
      stderr += chunk
    })

    python.on('error', (error) => {
      console.error('Python process error:', error)
      reject({ success: false, error: error.message })
    })

    python.on('close', (code, signal) => {
      console.log('Python process closed with code:', code, 'signal:', signal)
      console.log('Full stdout:', stdout)
      console.log('Full stderr:', stderr)

      if (code === 0) {
        resolve({ success: true })
      } else {
        const errorMsg = stderr || `Process exited with code ${code}`
        reject({ success: false, error: errorMsg })
      }
    })
  })
})

ipcMain.handle('check-ffmpeg', async () => {
  return new Promise((resolve) => {
    const ffmpeg = spawn('ffmpeg', ['-version'])
    ffmpeg.on('close', (code) => resolve(code === 0))
    ffmpeg.on('error', () => resolve(false))
  })
})

app.whenReady().then(() => {
  // Set default output directory
  if (!store.has('defaultOutputDir')) {
    store.set('defaultOutputDir', path.join(os.homedir(), 'TikTok_Output'))
  }
  createWindow()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})
