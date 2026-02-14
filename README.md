# TikTok Video Processor 🎬

A modern, beautiful desktop application for batch processing videos to TikTok format (9:16 aspect ratio, 1080x1920) with custom text overlays.

## Features

✨ **Modern UI** - Beautiful, fluid interface with smooth animations and gradients
🎨 **5 Font Choices** - Choose from carefully selected fonts for your text overlays
💾 **Persistent Settings** - Automatically remembers your last export folder and font preference
📹 **Batch Processing** - Process multiple videos at once
🎯 **Smart Zoom** - Automatically crops and scales videos to perfect TikTok format
📝 **Custom Captions** - Add text overlays to individual videos or bulk apply
🚀 **No Console Window** - Clean, professional app experience

## Prerequisites

Before running the app, you need to have:

1. **Node.js** (v18 or higher)
   - Download from [nodejs.org](https://nodejs.org/)

2. **Python** (v3.8 or higher)
   - Download from [python.org](https://www.python.org/)
   - Make sure Python is added to your PATH during installation

3. **FFmpeg**
   - **Windows**:
     ```bash
     winget install ffmpeg
     # or
     choco install ffmpeg
     ```
   - **macOS**:
     ```bash
     brew install ffmpeg
     ```
   - **Linux**:
     ```bash
     sudo apt install ffmpeg
     ```

## Installation

1. **Install Dependencies**
   ```bash
   npm install
   ```

   This will install all Node.js packages including React, Electron, Tailwind, etc.

2. **Run Development Mode**
   ```bash
   npm run dev
   ```

   This will start the Vite dev server and automatically launch Electron with hot-reload enabled.

3. **Build for Production**
   ```bash
   npm run build        # Build for current platform
   npm run build:win    # Build for Windows specifically
   ```

   The built app will be in the `release` folder. You'll get an installer ready to distribute!

## Usage

1. **Add Videos** - Click the "Add Videos" button to select video files
2. **Add Captions** - Click on a video to select it, then type your caption in the right panel
3. **Bulk Caption** - Use the "Bulk Caption" section to apply the same caption to all videos
4. **Choose Font** - Click the Settings button to select your preferred font style
5. **Set Output Folder** - Choose where your processed videos will be saved
6. **Process** - Click "Process All Videos" to start batch processing

## Font Options

- **Impact** - Classic, bold impact (default TikTok style)
- **Arial Black** - Strong, readable, modern
- **Montserrat** - Clean, professional sans-serif
- **Bebas Neue** - Tall, condensed, attention-grabbing
- **Oswald** - Bold, geometric, contemporary

## Project Structure

```
tt-processor/
├── electron/          # Electron main process
│   ├── main.ts       # Main window & IPC handlers
│   └── preload.ts    # Preload script for security
├── python/           # Python video processing
│   └── processor.py  # FFmpeg video processor
├── src/              # React frontend
│   ├── components/   # UI components
│   ├── App.tsx       # Main app component
│   ├── types.ts      # TypeScript types
│   └── index.css     # Global styles (Tailwind)
├── package.json      # Node dependencies & scripts
└── vite.config.ts    # Vite build configuration
```

## Technical Details

- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Animations**: Framer Motion
- **Desktop**: Electron
- **Backend**: Python + FFmpeg
- **Storage**: electron-store for persistent settings

## Troubleshooting

### FFmpeg not found
Make sure FFmpeg is installed and available in your PATH. Run `ffmpeg -version` in your terminal to verify.

### Videos not processing
1. Check that the input videos are in a supported format (MP4, MOV, AVI, MKV, etc.)
2. Ensure you have write permissions to the output folder
3. Check that there's enough disk space

### App won't start
1. Make sure all dependencies are installed: `npm install`
2. Verify Node.js version: `node --version` (should be v18+)
3. Try deleting `node_modules` and running `npm install` again

## Development

To contribute or modify:

```bash
# Install dependencies
npm install

# Run in development mode (hot reload)
npm run dev

# Build for production
npm run build

# Build for Windows only
npm run build:win
```

## License

MIT License - Feel free to use and modify!

## Credits

Built with ❤️ using Electron, React, TypeScript, and FFmpeg
