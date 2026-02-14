import { useState } from 'react'
import { motion } from 'framer-motion'
import { X, Type } from 'lucide-react'
import { Settings, AVAILABLE_FONTS } from '../types'

interface SettingsPanelProps {
  settings: Settings
  onClose: () => void
  onSave: (settings: Settings) => void
}

export default function SettingsPanel({ settings, onClose, onSave }: SettingsPanelProps) {
  const [localSettings, setLocalSettings] = useState(settings)

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
      />

      {/* Panel */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="fixed inset-0 m-auto w-full max-w-2xl h-fit z-50"
      >
        <div className="card mx-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-dark-800">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center">
                <Type className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-2xl font-bold">Settings</h2>
            </div>
            <button
              onClick={onClose}
              className="text-dark-400 hover:text-white transition-colors p-2 hover:bg-dark-800 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="space-y-6">
            {/* Font Selection */}
            <div>
              <h3 className="font-semibold mb-4">Text Overlay Font</h3>
              <div className="grid grid-cols-1 gap-3">
                {AVAILABLE_FONTS.map((font) => (
                  <label
                    key={font.value}
                    className={`
                      relative flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-all
                      ${
                        localSettings.selectedFont === font.value
                          ? 'bg-primary-500/10 border-primary-500 shadow-lg shadow-primary-500/20'
                          : 'bg-dark-800 border-dark-700 hover:border-dark-600'
                      }
                    `}
                  >
                    <input
                      type="radio"
                      name="font"
                      value={font.value}
                      checked={localSettings.selectedFont === font.value}
                      onChange={(e) =>
                        setLocalSettings({ ...localSettings, selectedFont: e.target.value })
                      }
                      className="sr-only"
                    />
                    <div className={`
                      w-5 h-5 rounded-full border-2 flex items-center justify-center
                      ${
                        localSettings.selectedFont === font.value
                          ? 'border-primary-500'
                          : 'border-dark-600'
                      }
                    `}>
                      {localSettings.selectedFont === font.value && (
                        <div className="w-2.5 h-2.5 rounded-full bg-primary-500" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">{font.name}</div>
                      <div className={`text-2xl mt-2 ${font.preview}`}>
                        Sample Text Preview
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Info */}
            <div className="bg-dark-800/50 border border-dark-700 rounded-xl p-4">
              <p className="text-sm text-dark-300">
                💡 The selected font will be used for text overlays on all processed videos.
                Choose a font that matches your content style!
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex gap-3 mt-6 pt-4 border-t border-dark-800">
            <button onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
            <button
              onClick={() => onSave(localSettings)}
              className="btn-primary flex-1"
            >
              Save Settings
            </button>
          </div>
        </div>
      </motion.div>
    </>
  )
}
