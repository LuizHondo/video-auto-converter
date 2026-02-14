import { motion } from 'framer-motion'
import { Video, Trash2, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import { VideoItem } from '../types'

interface VideoCardProps {
  video: VideoItem
  isSelected: boolean
  onSelect: () => void
  onRemove: () => void
}

export default function VideoCard({ video, isSelected, onSelect, onRemove }: VideoCardProps) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      onClick={onSelect}
      className={`
        relative p-4 rounded-xl border cursor-pointer transition-all duration-200
        ${
          isSelected
            ? 'bg-dark-800 border-primary-500 shadow-lg shadow-primary-500/20'
            : 'bg-dark-900 border-dark-700 hover:border-dark-600 hover:bg-dark-850'
        }
      `}
    >
      <div className="flex items-start gap-3">
        <div className={`
          w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
          ${isSelected ? 'bg-primary-500/20' : 'bg-dark-800'}
        `}>
          <Video className={`w-5 h-5 ${isSelected ? 'text-primary-400' : 'text-dark-400'}`} />
        </div>

        <div className="flex-1 min-w-0">
          <h4 className="font-medium truncate">{video.filename}</h4>
          <p className="text-sm text-dark-400 truncate mt-1">
            {video.caption || 'No caption'}
          </p>

          <div className="flex items-center gap-2 mt-2">
            {video.status === 'completed' && (
              <span className="flex items-center gap-1 text-xs text-green-400">
                <CheckCircle className="w-3 h-3" />
                Completed
              </span>
            )}
            {video.status === 'processing' && (
              <span className="flex items-center gap-1 text-xs text-blue-400">
                <Loader className="w-3 h-3 animate-spin" />
                Processing {video.progress.toFixed(0)}%
              </span>
            )}
            {video.status === 'error' && (
              <span className="flex items-center gap-1 text-xs text-red-400">
                <AlertCircle className="w-3 h-3" />
                Error
              </span>
            )}
            {video.status === 'pending' && (
              <span className="text-xs text-yellow-400">Pending</span>
            )}
          </div>

          {video.status === 'processing' && (
            <div className="mt-2 h-1 bg-dark-700 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-primary-500 to-primary-600"
                initial={{ width: 0 }}
                animate={{ width: `${video.progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          )}
        </div>

        <button
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          className="text-dark-400 hover:text-red-400 transition-colors p-1 rounded-lg hover:bg-dark-800"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  )
}
