#!/usr/bin/env python3
"""
TikTok Video Processor - CLI Version
Processes a single video to TikTok format with text overlay.
"""

import sys
import subprocess
import json
import re
import os
import textwrap
import tempfile


class FFmpegProcessor:
    """Handles FFmpeg operations for video processing."""

    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    TARGET_FPS = 30
    VIDEO_BITRATE = "6M"
    AUDIO_BITRATE = "192k"

    @classmethod
    def get_video_info(cls, filepath: str) -> dict:
        """Get video metadata using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                filepath
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                video_stream = None
                for stream in data.get("streams", []):
                    if stream.get("codec_type") == "video":
                        video_stream = stream
                        break
                if video_stream:
                    duration = float(data.get("format", {}).get("duration", 0))
                    return {
                        "width": int(video_stream.get("width", 0)),
                        "height": int(video_stream.get("height", 0)),
                        "duration": duration,
                    }
        except Exception as e:
            print(f"ERROR: Failed to get video info: {e}", file=sys.stderr)
        return {"width": 0, "height": 0, "duration": 0}

    @classmethod
    def process_video(cls, input_path: str, output_path: str, caption: str = "", font: str = "Impact") -> bool:
        """
        Process a single video: smart zoom to 9:16 + text overlay.
        """
        tw, th = cls.TARGET_WIDTH, cls.TARGET_HEIGHT
        target_ratio = tw / th

        info = cls.get_video_info(input_path)
        src_w = info["width"]
        src_h = info["height"]
        duration = info["duration"]

        if src_w == 0 or src_h == 0:
            print("ERROR: Could not determine video dimensions", file=sys.stderr)
            return False

        src_ratio = src_w / src_h if src_h > 0 else 1.0

        # Build scale + crop filter (ensure even dimensions)
        if src_ratio > target_ratio:
            # Source is wider - scale height to target, width auto (ensure even)
            scale_filter = f"scale=-2:{th}:flags=lanczos"
        else:
            # Source is taller - scale width to target, height auto (ensure even)
            scale_filter = f"scale={tw}:-2:flags=lanczos"

        # Crop to exact target size, centered
        crop_filter = f"crop={tw}:{th}:(iw-{tw})/2:(ih-{th})/2"

        # Build text overlay filter
        text_filter = ""
        text_file = None
        if caption.strip():
            # Clean caption: remove any existing newlines/line breaks from the input
            # This ensures we only have our controlled line breaks
            caption = caption.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
            # Normalize multiple spaces to single space
            caption = ' '.join(caption.split())

            # Dynamic font size based on text length
            text_length = len(caption)
            if text_length < 30:
                fontsize = 40
            elif text_length < 60:
                fontsize = 35
            elif text_length < 100:
                fontsize = 30
            else:
                fontsize = 25

            text_y = int(th * 0.20)  # Position from top

            # Map font names to system fonts
            font_map = {
                'Impact': 'Impact',
                'Arial-Black': 'Arial Black',
                'Montserrat-Bold': 'Montserrat',
                'Bebas-Neue': 'Arial Black',  # Fallback
                'Oswald-Bold': 'Arial Black',  # Fallback
            }
            font_name = font_map.get(font, 'Impact')

            # Escape font name if it contains spaces (for FFmpeg filter syntax)
            font_name_escaped = font_name.replace(' ', '\\ ')

            # Escape special characters in text for FFmpeg filter syntax
            text_escaped = (caption
                .replace('\\', '\\\\')  # Backslash must be first
                .replace(':', '\\:')
                .replace("'", "\\'"))

            # Use text parameter with escaped content
            text_filter = (
                f",drawtext=text='{text_escaped}'"
                f":fontsize={fontsize}"
                f":fontcolor=white"
                f":borderw=3"
                f":bordercolor=black@0.9"
                f":x=(w-text_w)/2"
                f":y={text_y}"
                f":font={font_name_escaped}"
                f":line_spacing=8"
                f":box=1"
                f":boxcolor=black@0.7"
                f":boxborderw=15"
            )

        vf = f"{scale_filter},{crop_filter}{text_filter}"

        # Debug: Print the filter chain
        print(f"Video filter: {vf}", flush=True)

        # Simple, reliable FFmpeg command without conflicts
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", vf,
            # Video encoding - use CRF only (don't mix with bitrate)
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",  # Good quality, compatible
            # Audio encoding - simple copy or encode
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            # Output settings
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            # Don't use -map to avoid stream conflicts
            output_path
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )

            stderr_output = []
            last_progress = 0

            # Read stderr for progress updates
            for line in process.stderr:
                stderr_output.append(line)
                # FFmpeg outputs progress info to stderr with time=
                if "time=" in line and duration > 0:
                    match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                    if match:
                        h, m, s = match.groups()
                        current = int(h) * 3600 + int(m) * 60 + float(s)
                        # Cap at 95% until process actually finishes
                        pct = min((current / duration) * 100, 95.0)
                        if pct > last_progress:
                            last_progress = pct
                            print(f"PROGRESS: {pct:.1f}", flush=True)

            # Wait for process to fully complete
            process.wait()

            if process.returncode != 0:
                error = "".join(stderr_output[-10:])
                print(f"ERROR: FFmpeg failed:\n{error}", file=sys.stderr)
                return False

            # Only report 100% after process successfully completes
            print("PROGRESS: 100.0", flush=True)

            return True

        except Exception as e:
            print(f"ERROR: Exception during processing: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()

            return False


def main():
    if len(sys.argv) < 3:
        print("Usage: processor.py <input_path> <output_path> [caption] [font]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    caption = sys.argv[3] if len(sys.argv) > 3 else ""
    font = sys.argv[4] if len(sys.argv) > 4 else "Impact"

    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print(f"Processing: {input_path}", flush=True)
    print(f"Output: {output_path}", flush=True)
    print(f"Caption: {caption or '(none)'}", flush=True)
    print(f"Font: {font}", flush=True)

    success = FFmpegProcessor.process_video(input_path, output_path, caption, font)

    if success:
        print("SUCCESS: Video processed successfully", flush=True)
        sys.exit(0)
    else:
        print("FAILED: Video processing failed", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
