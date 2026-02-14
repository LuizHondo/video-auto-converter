# 🚀 Start Here - Get Running in 2 Minutes!

I've fixed the build issues! Here's how to get started:

## Quick Start (Copy & Paste These Commands)

Open your terminal in this folder and run:

```bash
# Step 1: Install all dependencies (this takes 1-2 minutes)
npm install

# Step 2: Run the app!
npm run dev
```

That's it! The app will automatically:

- ✅ Compile all TypeScript code
- ✅ Start the development server
- ✅ Launch the Electron window
- ✅ Enable hot-reload (changes appear instantly)

## What I Fixed

The original configuration had some compatibility issues. I've updated it to use a simpler, more modern setup:

✅ **Changed to ES modules** - Added `"type": "module"` to package.json
✅ **Integrated vite-plugin-electron** - Automatically compiles Electron + React together
✅ **Simplified dev script** - Just `npm run dev` instead of multiple commands
✅ **Fixed path resolution** - Python script paths work in both dev and production

## Verify It's Working

When you run `npm run dev`, you should see:

1. Terminal shows Vite starting up
2. Terminal shows Electron compiling
3. A beautiful dark-themed window opens
4. The app is ready to use!

## If You Get Errors

**"Module not found"**: Run `npm install` again

**"FFmpeg not found"**: Install FFmpeg:

```bash
# Windows
winget install ffmpeg
```

**Port already in use**: Close any other apps using port 5173

## Next Steps

1. Click **"Add Videos"** to select video files
2. Click **Settings** to choose your favorite font
3. Add captions to your videos
4. Click **"Process All Videos"** to convert them!

## Build for Distribution

When you're ready to create an installer:

```bash
npm run build:win
```

The installer will be in the `release` folder.

---

**Need more details?** Check out:

- 📖 [README.md](README.md) - Full documentation
- ⚡ [QUICKSTART.md](QUICKSTART.md) - Detailed setup guide

Happy video processing! 🎬✨
