// Preload script - must be CommonJS
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  selectVideos: () => ipcRenderer.invoke('select-videos'),
  getSetting: (key) => ipcRenderer.invoke('get-setting', key),
  setSetting: (key, value) => ipcRenderer.invoke('set-setting', key, value),
  processVideo: (args) => ipcRenderer.invoke('process-video', args),
  checkFFmpeg: () => ipcRenderer.invoke('check-ffmpeg'),
  onProcessingProgress: (callback) => {
    ipcRenderer.on('processing-progress', (_, data) => callback(data))
  },
})
