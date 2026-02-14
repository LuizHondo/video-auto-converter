export interface VideoItem {
  id: string
  filepath: string
  filename: string
  caption: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  duration: number
  width: number
  height: number
  progress: number
  errorMsg?: string
}

export interface Settings {
  outputDir: string
  selectedFont: string
  theme: 'dark' | 'light'
}

export const AVAILABLE_FONTS = [
  { name: 'Impact', value: 'Impact', preview: 'font-impact' },
  { name: 'Arial Black', value: 'Arial-Black', preview: 'font-arial-black' },
  { name: 'Montserrat', value: 'Montserrat-Bold', preview: 'font-montserrat' },
  { name: 'Bebas Neue', value: 'Bebas-Neue', preview: 'font-bebas' },
  { name: 'Oswald', value: 'Oswald-Bold', preview: 'font-oswald' },
]

declare global {
  interface Window {
    electronAPI: {
      selectFolder: () => Promise<string | null>
      selectVideos: () => Promise<string[]>
      getSetting: (key: string) => Promise<any>
      setSetting: (key: string, value: any) => Promise<boolean>
      processVideo: (args: {
        inputPath: string
        outputPath: string
        caption: string
        font: string
      }) => Promise<{ success: boolean; error?: string }>
      checkFFmpeg: () => Promise<boolean>
      onProcessingProgress: (callback: (data: { path: string; progress: number }) => void) => void
    }
  }
}

export {}
