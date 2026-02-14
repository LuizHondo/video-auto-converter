import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Film, FolderOpen, Plus, Trash2, Play, Settings as SettingsIcon,
  X, CheckCircle, AlertCircle, Loader
} from 'lucide-react'
import { VideoItem, Settings, AVAILABLE_FONTS } from './types'
import VideoCard from './components/VideoCard'
import SettingsPanel from './components/SettingsPanel'

function App() {
  const [videos, setVideos] = useState<VideoItem[]>([])
  const [settings, setSettings] = useState<Settings>({
    outputDir: '',
    selectedFont: 'Impact',
    theme: 'dark',
  })
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [bulkCaption, setBulkCaption] = useState('')

  useEffect(() => {
    // Load settings
    const loadSettings = async () => {
      const outputDir = await window.electronAPI.getSetting('outputDir')
      const selectedFont = await window.electronAPI.getSetting('selectedFont')
      const defaultDir = await window.electronAPI.getSetting('defaultOutputDir')

      setSettings({
        outputDir: outputDir || defaultDir || 'TikTok_Output',
        selectedFont: selectedFont || 'Impact',
        theme: 'dark',
      })
    }
    loadSettings()

    // Check FFmpeg
    window.electronAPI.checkFFmpeg().then((available) => {
      if (!available) {
        alert('FFmpeg is not installed. Please install FFmpeg to process videos.')
      }
    })

    // Listen for progress updates
    window.electronAPI.onProcessingProgress((data) => {
      setVideos((prev) =>
        prev.map((v) =>
          v.filepath === data.path
            ? { ...v, progress: data.progress }
            : v
        )
      )
    })
  }, [])

  const handleAddVideos = async () => {
    const files = await window.electronAPI.selectVideos()
    if (files.length === 0) return

    const newVideos: VideoItem[] = files.map((filepath) => ({
      id: `${Date.now()}-${Math.random()}`,
      filepath,
      filename: filepath.split(/[\\/]/).pop() || '',
      caption: '',
      status: 'pending' as const,
      duration: 0,
      width: 0,
      height: 0,
      progress: 0,
    }))

    setVideos((prev) => [...prev, ...newVideos])
  }

  const handleRemoveVideo = (id: string) => {
    setVideos((prev) => prev.filter((v) => v.id !== id))
    if (selectedVideo === id) {
      setSelectedVideo(null)
    }
  }

  const handleClearAll = () => {
    if (videos.length > 0 && confirm('Clear all videos?')) {
      setVideos([])
      setSelectedVideo(null)
    }
  }

  const handleChooseOutputDir = async () => {
    const dir = await window.electronAPI.selectFolder()
    if (dir) {
      setSettings((prev) => ({ ...prev, outputDir: dir }))
      await window.electronAPI.setSetting('outputDir', dir)
    }
  }

  const handleUpdateCaption = (id: string, caption: string) => {
    setVideos((prev) =>
      prev.map((v) => (v.id === id ? { ...v, caption } : v))
    )
  }

  const handleApplyBulkCaption = () => {
    if (!bulkCaption.trim()) return

    setVideos((prev) =>
      prev.map((v) => (v.caption.trim() === '' ? { ...v, caption: bulkCaption } : v))
    )

    alert(`Caption applied to videos without captions!`)
  }

  const handleProcessAll = async () => {
    const pending = videos.filter((v) => v.status === 'pending' || v.status === 'error')
    if (pending.length === 0) {
      alert('No videos to process!')
      return
    }

    setIsProcessing(true)

    for (const video of pending) {
      setVideos((prev) =>
        prev.map((v) =>
          v.id === video.id ? { ...v, status: 'processing', progress: 0 } : v
        )
      )

      try {
        const outputPath = `${settings.outputDir}/${video.filename.replace(/\.[^/.]+$/, '')}_tiktok.mp4`

        await window.electronAPI.processVideo({
          inputPath: video.filepath,
          outputPath,
          caption: video.caption,
          font: settings.selectedFont,
        })

        setVideos((prev) =>
          prev.map((v) =>
            v.id === video.id ? { ...v, status: 'completed', progress: 100 } : v
          )
        )
      } catch (error: any) {
        const errorMsg = error.error || 'Processing failed'
        setVideos((prev) =>
          prev.map((v) =>
            v.id === video.id
              ? { ...v, status: 'error', errorMsg }
              : v
          )
        )

        // Show error dialog for Python not found
        if (errorMsg.includes('Python not found')) {
          alert('⚠️ Python Not Found\n\n' + errorMsg + '\n\nPlease install Python from python.org and restart the app.')
          break // Stop processing
        }
      }
    }

    setIsProcessing(false)
    alert('Processing complete!')
  }

  const selectedVideoData = videos.find((v) => v.id === selectedVideo)
  const pendingCount = videos.filter((v) => v.status === 'pending').length
  const completedCount = videos.filter((v) => v.status === 'completed').length

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-dark-950 via-dark-900 to-dark-950">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="border-b border-dark-800 bg-dark-900/50 backdrop-blur-xl"
      >
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
                <Film className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-dark-300 bg-clip-text text-transparent">
                  TikTok Video Processor
                </h1>
                <p className="text-sm text-dark-400">Convert videos to 9:16 format with captions</p>
              </div>
            </div>
            <button
              onClick={() => setShowSettings(true)}
              className="btn-secondary flex items-center gap-2"
            >
              <SettingsIcon className="w-4 h-4" />
              Settings
            </button>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Video List */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="w-1/2 border-r border-dark-800 flex flex-col"
        >
          <div className="p-4 border-b border-dark-800 bg-dark-900/30">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Video Queue</h2>
              <div className="flex gap-2">
                <button onClick={handleAddVideos} className="btn-primary flex items-center gap-2">
                  <Plus className="w-4 h-4" />
                  Add Videos
                </button>
                <button onClick={handleClearAll} className="btn-secondary">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm text-dark-400">
              <span>{videos.length} total</span>
              <span className="text-yellow-400">{pendingCount} pending</span>
              <span className="text-green-400">{completedCount} completed</span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            <AnimatePresence>
              {videos.map((video) => (
                <VideoCard
                  key={video.id}
                  video={video}
                  isSelected={selectedVideo === video.id}
                  onSelect={() => setSelectedVideo(video.id)}
                  onRemove={() => handleRemoveVideo(video.id)}
                />
              ))}
            </AnimatePresence>
            {videos.length === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center h-full text-dark-500"
              >
                <Film className="w-16 h-16 mb-4 opacity-20" />
                <p>No videos added yet</p>
                <p className="text-sm">Click "Add Videos" to get started</p>
              </motion.div>
            )}
          </div>
        </motion.div>

        {/* Right Panel - Details & Caption Editor */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="w-1/2 flex flex-col"
        >
          <div className="p-6 space-y-6 flex-1 overflow-y-auto">
            {selectedVideoData ? (
              <>
                <div className="card space-y-3">
                  <h3 className="font-semibold text-lg">Video Details</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-dark-400">File:</span>
                      <span className="font-medium truncate max-w-xs">{selectedVideoData.filename}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Status:</span>
                      <span className="flex items-center gap-1">
                        {selectedVideoData.status === 'completed' && (
                          <>
                            <CheckCircle className="w-4 h-4 text-green-400" />
                            <span className="text-green-400">Completed</span>
                          </>
                        )}
                        {selectedVideoData.status === 'processing' && (
                          <>
                            <Loader className="w-4 h-4 text-blue-400 animate-spin" />
                            <span className="text-blue-400">Processing {selectedVideoData.progress.toFixed(0)}%</span>
                          </>
                        )}
                        {selectedVideoData.status === 'error' && (
                          <>
                            <AlertCircle className="w-4 h-4 text-red-400" />
                            <span className="text-red-400">Error</span>
                          </>
                        )}
                        {selectedVideoData.status === 'pending' && (
                          <span className="text-yellow-400">Pending</span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="card space-y-3">
                  <h3 className="font-semibold">Caption (Text Overlay)</h3>
                  <textarea
                    value={selectedVideoData.caption}
                    onChange={(e) => handleUpdateCaption(selectedVideoData.id, e.target.value)}
                    placeholder="Enter caption text..."
                    className="textarea h-24"
                  />
                  <p className="text-xs text-dark-400">This text will appear at the top of the video</p>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-dark-500">
                <FolderOpen className="w-16 h-16 mb-4 opacity-20" />
                <p>No video selected</p>
                <p className="text-sm">Select a video to edit its caption</p>
              </div>
            )}

            <div className="card space-y-3">
              <h3 className="font-semibold">Bulk Caption</h3>
              <textarea
                value={bulkCaption}
                onChange={(e) => setBulkCaption(e.target.value)}
                placeholder="Enter caption to apply to all videos without one..."
                className="textarea h-20"
              />
              <button
                onClick={handleApplyBulkCaption}
                className="btn-secondary w-full"
                disabled={!bulkCaption.trim()}
              >
                Apply to All Empty Captions
              </button>
            </div>

            <div className="card space-y-3">
              <h3 className="font-semibold">Output Directory</h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={settings.outputDir}
                  readOnly
                  className="input flex-1 text-sm"
                />
                <button onClick={handleChooseOutputDir} className="btn-secondary">
                  <FolderOpen className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Process Button */}
          <div className="p-6 border-t border-dark-800 bg-dark-900/30">
            <button
              onClick={handleProcessAll}
              disabled={isProcessing || videos.length === 0}
              className="btn-primary w-full py-4 text-lg flex items-center justify-center gap-2"
            >
              {isProcessing ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Process All Videos
                </>
              )}
            </button>
          </div>
        </motion.div>
      </div>

      {/* Settings Modal */}
      <AnimatePresence>
        {showSettings && (
          <SettingsPanel
            settings={settings}
            onClose={() => setShowSettings(false)}
            onSave={async (newSettings) => {
              setSettings(newSettings)
              await window.electronAPI.setSetting('selectedFont', newSettings.selectedFont)
              setShowSettings(false)
            }}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
