# Quick Start Guide 🚀

Get up and running in 5 minutes!

## Step 1: Install Prerequisites

### Windows

Open PowerShell as Administrator and run:

```powershell
# Install FFmpeg
winget install ffmpeg

# Verify installations
node --version   # Should show v18 or higher
python --version # Should show Python 3.8 or higher
ffmpeg -version  # Should show FFmpeg version
```

### macOS

```bash
# Install FFmpeg
brew install ffmpeg

# Verify installations
node --version   # Should show v18 or higher
python3 --version # Should show Python 3.8 or higher
ffmpeg -version  # Should show FFmpeg version
```

### Linux (Ubuntu/Debian)

```bash
# Install FFmpeg
sudo apt update
sudo apt install ffmpeg

# Verify installations
node --version   # Should show v18 or higher
python3 --version # Should show Python 3.8 or higher
ffmpeg -version  # Should show FFmpeg version
```

## Step 2: Install App Dependencies

```bash
cd tt-processor
npm install
```

This will install all required packages (React, Electron, Tailwind CSS, etc.)

## Step 3: Run the App

### Development Mode (for testing)

```bash
npm run dev
```

This single command will:
- Start the Vite development server
- Compile the Electron TypeScript code
- Launch the Electron app automatically
- Enable hot-reload for instant updates when you make changes

### Production Build (for distribution)

```bash
npm run build
```

The built app will be in the `release` folder. Double-click the installer to install!

## First Time Setup

1. **Launch the app** - It will open with an empty video queue
2. **Click Settings** - Choose your preferred font for text overlays
3. **Set Output Folder** - Choose where you want processed videos saved
   - The app will remember this folder for next time!
4. **You're ready!** - Start adding and processing videos

## Tips & Tricks

💡 **Font Selection**: Each font has a different style:
   - Impact: Bold, classic TikTok
   - Arial Black: Modern, clean
   - Montserrat: Professional, elegant
   - Bebas Neue: Tall, eye-catching
   - Oswald: Geometric, contemporary

💡 **Bulk Caption**: Perfect when you want the same text on multiple videos

💡 **Individual Captions**: Click a video to add a unique caption just for that one

💡 **Persistent Settings**: Your output folder and font choice are saved automatically!

## Need Help?

- **FFmpeg errors**: Make sure FFmpeg is in your PATH
- **App won't start**: Try `npm install` again
- **Videos not processing**: Check file permissions and disk space

## What's Different from the Old Version?

✨ **New Features**:
- Beautiful modern UI with animations
- 5 font choices (was hardcoded to Impact)
- Remembers last export folder
- No console window
- Better progress tracking
- Smoother, more responsive

📁 **Old version**: Saved as `tiktok_processor_old.py` if you need it

Enjoy! 🎉
