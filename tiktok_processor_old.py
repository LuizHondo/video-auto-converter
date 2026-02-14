#!/usr/bin/env python3
"""
TikTok Video Processor
======================
Desktop application for batch processing videos to TikTok format (9:16, 1080x1920).
Features: smart zoom/crop, custom text overlays, batch queue, progress tracking.

Requirements:
    - Python 3.8+
    - FFmpeg installed and available in PATH
    - tkinter (usually included with Python)

Usage:
    python tiktok_processor.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import json
import shutil
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
import tempfile


# ─────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────

@dataclass
class VideoItem:
    filepath: str
    caption: str = ""
    status: str = "Pendente"  # Pendente, Processando, Concluído, Erro
    duration: float = 0.0
    width: int = 0
    height: int = 0
    error_msg: str = ""

    @property
    def filename(self) -> str:
        return os.path.basename(self.filepath)

    @property
    def resolution_str(self) -> str:
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "N/A"

    @property
    def duration_str(self) -> str:
        if self.duration > 0:
            mins = int(self.duration // 60)
            secs = int(self.duration % 60)
            return f"{mins:02d}:{secs:02d}"
        return "N/A"


# ─────────────────────────────────────────────
# FFmpeg Utilities
# ─────────────────────────────────────────────

class FFmpegProcessor:
    """Handles all FFmpeg operations for video processing."""

    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    TARGET_FPS = 30
    VIDEO_BITRATE = "6M"
    AUDIO_BITRATE = "192k"

    @staticmethod
    def check_ffmpeg() -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def get_video_info(filepath: str) -> dict:
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
        except Exception:
            pass
        return {"width": 0, "height": 0, "duration": 0}

    @classmethod
    def process_video(cls, item: VideoItem, output_path: str,
                      progress_callback=None) -> bool:
        """
        Process a single video: smart zoom to 9:16 + text overlay.
        
        Strategy:
        - Scale video so the smaller dimension fills the target frame
        - Center crop to 1080x1920
        - Add caption text with semi-transparent background at the top
        """
        tw, th = cls.TARGET_WIDTH, cls.TARGET_HEIGHT
        target_ratio = tw / th  # 0.5625

        src_w, src_h = item.width, item.height
        if src_w == 0 or src_h == 0:
            info = cls.get_video_info(item.filepath)
            src_w = info["width"]
            src_h = info["height"]

        src_ratio = src_w / src_h if src_h > 0 else 1.0

        # Build the scale + crop filter for smart zoom
        if src_ratio > target_ratio:
            # Source is wider → scale height to fill, crop width
            scale_filter = f"scale=-2:{th}"
        else:
            # Source is taller or equal → scale width to fill, crop height
            scale_filter = f"scale={tw}:-2"

        crop_filter = f"crop={tw}:{th}"

        # Build text overlay filter
        caption = item.caption.strip()
        text_filter = ""
        if caption:
            # Escape special characters for FFmpeg drawtext
            safe_caption = (caption
                            .replace("\\", "\\\\\\\\")
                            .replace("'", "\u2019")
                            .replace('"', '\\"')
                            .replace(":", "\\:")
                            .replace("%", "%%"))

            # Position at 30% from top (576px for 1920px height)
            box_y = int(th * 0.30) - 60  # Center the box around 30% mark
            text_y = int(th * 0.30)

            text_filter = (
                f",drawbox=y={box_y}:w=iw:h=140:color=black@0.6:t=fill,"
                f"drawtext=text='{safe_caption}'"
                f":fontsize=52"
                f":fontcolor=white"
                f":borderw=3"
                f":bordercolor=black@0.9"
                f":x=(w-text_w)/2"
                f":y={text_y}"
                f":font='Impact'"
            )

        vf = f"{scale_filter},{crop_filter}{text_filter}"

        cmd = [
            "ffmpeg", "-y",
            "-i", item.filepath,
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "18",
            "-maxrate", cls.VIDEO_BITRATE,
            "-bufsize", "12M",
            "-r", str(cls.TARGET_FPS),
            "-c:a", "aac",
            "-b:a", cls.AUDIO_BITRATE,
            "-ar", "44100",
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            output_path
        ]

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Read stderr for progress
            duration = item.duration if item.duration > 0 else 1.0
            stderr_output = []
            for line in process.stderr:
                stderr_output.append(line)
                if progress_callback and "time=" in line:
                    match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                    if match:
                        h, m, s = match.groups()
                        current = int(h) * 3600 + int(m) * 60 + float(s)
                        pct = min(current / duration * 100, 99.0)
                        progress_callback(pct)

            process.wait()

            if process.returncode != 0:
                error = "".join(stderr_output[-5:])
                raise RuntimeError(f"FFmpeg error (code {process.returncode}):\n{error}")

            if progress_callback:
                progress_callback(100.0)
            return True

        except Exception as e:
            item.error_msg = str(e)
            return False


# ─────────────────────────────────────────────
# Main Application UI
# ─────────────────────────────────────────────

class TikTokProcessorApp:
    """Main application window."""

    # Color scheme
    BG_PRIMARY = "#1a1a2e"
    BG_SECONDARY = "#16213e"
    BG_CARD = "#0f3460"
    ACCENT = "#e94560"
    ACCENT_HOVER = "#ff6b81"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a8b2d1"
    SUCCESS = "#00d2d3"
    WARNING = "#feca57"
    ERROR = "#ff6b6b"

    SUPPORTED_FORMATS = [
        ("Vídeos", "*.mp4 *.mov *.avi *.mkv *.wmv *.flv *.webm"),
        ("MP4", "*.mp4"),
        ("MOV", "*.mov"),
        ("AVI", "*.avi"),
        ("Todos", "*.*"),
    ]

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TikTok Video Processor")
        self.root.geometry("1000x750")
        self.root.minsize(850, 650)
        self.root.configure(bg=self.BG_PRIMARY)

        self.video_items: List[VideoItem] = []
        self.output_dir: str = os.path.join(os.path.expanduser("~"), "TikTok_Output")
        self.is_processing = False
        self.selected_index: Optional[int] = None

        self._setup_styles()
        self._build_ui()
        self._check_ffmpeg()

    def _setup_styles(self):
        """Configure ttk styles."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure("Main.TFrame", background=self.BG_PRIMARY)
        self.style.configure("Card.TFrame", background=self.BG_SECONDARY)
        self.style.configure("Title.TLabel",
                             background=self.BG_PRIMARY,
                             foreground=self.ACCENT,
                             font=("Helvetica", 20, "bold"))
        self.style.configure("Subtitle.TLabel",
                             background=self.BG_PRIMARY,
                             foreground=self.TEXT_SECONDARY,
                             font=("Helvetica", 10))
        self.style.configure("Header.TLabel",
                             background=self.BG_SECONDARY,
                             foreground=self.TEXT_PRIMARY,
                             font=("Helvetica", 12, "bold"))
        self.style.configure("Info.TLabel",
                             background=self.BG_SECONDARY,
                             foreground=self.TEXT_SECONDARY,
                             font=("Helvetica", 10))
        self.style.configure("Status.TLabel",
                             background=self.BG_PRIMARY,
                             foreground=self.TEXT_SECONDARY,
                             font=("Helvetica", 9))

        # Buttons
        self.style.configure("Accent.TButton",
                             background=self.ACCENT,
                             foreground=self.TEXT_PRIMARY,
                             font=("Helvetica", 11, "bold"),
                             padding=(16, 8))
        self.style.map("Accent.TButton",
                       background=[("active", self.ACCENT_HOVER)])

        self.style.configure("Secondary.TButton",
                             background=self.BG_CARD,
                             foreground=self.TEXT_PRIMARY,
                             font=("Helvetica", 10),
                             padding=(12, 6))
        self.style.map("Secondary.TButton",
                       background=[("active", self.BG_SECONDARY)])

        # Progress bar
        self.style.configure("Custom.Horizontal.TProgressbar",
                             troughcolor=self.BG_SECONDARY,
                             background=self.ACCENT,
                             thickness=8)

        # Treeview
        self.style.configure("Custom.Treeview",
                             background=self.BG_SECONDARY,
                             foreground=self.TEXT_PRIMARY,
                             fieldbackground=self.BG_SECONDARY,
                             font=("Helvetica", 10),
                             rowheight=32)
        self.style.configure("Custom.Treeview.Heading",
                             background=self.BG_CARD,
                             foreground=self.TEXT_PRIMARY,
                             font=("Helvetica", 10, "bold"))
        self.style.map("Custom.Treeview",
                       background=[("selected", self.BG_CARD)],
                       foreground=[("selected", self.ACCENT)])

    def _build_ui(self):
        """Build the complete UI."""
        main = ttk.Frame(self.root, style="Main.TFrame")
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # ── Header ──
        header = ttk.Frame(main, style="Main.TFrame")
        header.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(header, text="🎬 TikTok Video Processor",
                  style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(header, text="Converta vídeos para formato TikTok (9:16) com legendas",
                  style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(16, 0), pady=(6, 0))

        # ── Toolbar ──
        toolbar = ttk.Frame(main, style="Main.TFrame")
        toolbar.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(toolbar, text="📂 Adicionar Vídeos",
                   style="Accent.TButton",
                   command=self._add_videos).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="🗑 Remover Selecionado",
                   style="Secondary.TButton",
                   command=self._remove_selected).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="🧹 Limpar Fila",
                   style="Secondary.TButton",
                   command=self._clear_queue).pack(side=tk.LEFT, padx=(0, 6))

        # Output directory selector
        dir_frame = ttk.Frame(toolbar, style="Main.TFrame")
        dir_frame.pack(side=tk.RIGHT)
        ttk.Button(dir_frame, text="📁 Pasta Destino",
                   style="Secondary.TButton",
                   command=self._choose_output_dir).pack(side=tk.LEFT, padx=(0, 6))
        self.dir_label = ttk.Label(dir_frame, text=self._short_path(self.output_dir),
                                   style="Status.TLabel")
        self.dir_label.pack(side=tk.LEFT)

        # ── Content area (paned) ──
        paned = ttk.PanedWindow(main, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Left: Video queue list
        left_frame = ttk.Frame(paned, style="Card.TFrame")
        paned.add(left_frame, weight=3)

        ttk.Label(left_frame, text="Fila de Vídeos",
                  style="Header.TLabel").pack(fill=tk.X, padx=10, pady=(10, 4))

        tree_frame = ttk.Frame(left_frame, style="Card.TFrame")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("filename", "resolution", "duration", "caption_preview", "status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                 style="Custom.Treeview", selectmode="browse")
        self.tree.heading("filename", text="Arquivo")
        self.tree.heading("resolution", text="Resolução")
        self.tree.heading("duration", text="Duração")
        self.tree.heading("caption_preview", text="Legenda")
        self.tree.heading("status", text="Status")

        self.tree.column("filename", width=180, minwidth=120)
        self.tree.column("resolution", width=80, minwidth=60, anchor="center")
        self.tree.column("duration", width=65, minwidth=50, anchor="center")
        self.tree.column("caption_preview", width=160, minwidth=80)
        self.tree.column("status", width=90, minwidth=70, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Right: Caption editor / info panel
        right_frame = ttk.Frame(paned, style="Card.TFrame")
        paned.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Detalhes & Legenda",
                  style="Header.TLabel").pack(fill=tk.X, padx=10, pady=(10, 4))

        # Info labels
        info_frame = ttk.Frame(right_frame, style="Card.TFrame")
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

        self.info_name = ttk.Label(info_frame, text="Nenhum vídeo selecionado",
                                   style="Info.TLabel")
        self.info_name.pack(anchor="w")
        self.info_details = ttk.Label(info_frame, text="",
                                      style="Info.TLabel")
        self.info_details.pack(anchor="w")

        # Caption input
        cap_label_frame = ttk.Frame(right_frame, style="Card.TFrame")
        cap_label_frame.pack(fill=tk.X, padx=10)
        ttk.Label(cap_label_frame, text="Legenda (texto no topo do vídeo):",
                  style="Info.TLabel").pack(anchor="w")

        self.caption_text = tk.Text(right_frame, height=4, wrap=tk.WORD,
                                    bg=self.BG_PRIMARY, fg=self.TEXT_PRIMARY,
                                    insertbackground=self.TEXT_PRIMARY,
                                    font=("Helvetica", 11),
                                    relief=tk.FLAT, padx=8, pady=6)
        self.caption_text.pack(fill=tk.X, padx=10, pady=(4, 8))
        self.caption_text.bind("<KeyRelease>", self._on_caption_change)

        ttk.Button(right_frame, text="💾 Salvar Legenda",
                   style="Secondary.TButton",
                   command=self._save_caption).pack(padx=10, anchor="w")

        # Bulk caption
        sep = ttk.Separator(right_frame, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, padx=10, pady=12)

        ttk.Label(right_frame,
                  text="Legenda em massa (aplicar a todos sem legenda):",
                  style="Info.TLabel").pack(fill=tk.X, padx=10)

        self.bulk_caption = tk.Text(right_frame, height=3, wrap=tk.WORD,
                                    bg=self.BG_PRIMARY, fg=self.TEXT_PRIMARY,
                                    insertbackground=self.TEXT_PRIMARY,
                                    font=("Helvetica", 11),
                                    relief=tk.FLAT, padx=8, pady=6)
        self.bulk_caption.pack(fill=tk.X, padx=10, pady=(4, 8))

        ttk.Button(right_frame, text="📝 Aplicar a Todos",
                   style="Secondary.TButton",
                   command=self._apply_bulk_caption).pack(padx=10, anchor="w")

        # ── Bottom: Progress & Process button ──
        bottom = ttk.Frame(main, style="Main.TFrame")
        bottom.pack(fill=tk.X, pady=(4, 0))

        # Progress
        prog_frame = ttk.Frame(bottom, style="Main.TFrame")
        prog_frame.pack(fill=tk.X, pady=(0, 6))

        self.progress_label = ttk.Label(prog_frame, text="Pronto",
                                        style="Status.TLabel")
        self.progress_label.pack(side=tk.LEFT)

        self.overall_label = ttk.Label(prog_frame, text="",
                                       style="Status.TLabel")
        self.overall_label.pack(side=tk.RIGHT)

        self.progress_bar = ttk.Progressbar(bottom, mode="determinate",
                                            style="Custom.Horizontal.TProgressbar",
                                            maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))

        # Process button
        btn_frame = ttk.Frame(bottom, style="Main.TFrame")
        btn_frame.pack(fill=tk.X)

        self.process_btn = ttk.Button(btn_frame,
                                      text="🚀 Processar Todos os Vídeos",
                                      style="Accent.TButton",
                                      command=self._start_processing)
        self.process_btn.pack(side=tk.RIGHT)

        self.video_count_label = ttk.Label(btn_frame, text="0 vídeos na fila",
                                           style="Status.TLabel")
        self.video_count_label.pack(side=tk.LEFT, pady=(4, 0))

    # ─────────────────────────────────────────
    # Actions
    # ─────────────────────────────────────────

    def _check_ffmpeg(self):
        """Verify FFmpeg is installed."""
        if not FFmpegProcessor.check_ffmpeg():
            messagebox.showwarning(
                "FFmpeg Não Encontrado",
                "FFmpeg não foi encontrado no sistema.\n\n"
                "Por favor instale o FFmpeg:\n"
                "• Windows: choco install ffmpeg  ou  winget install ffmpeg\n"
                "• macOS: brew install ffmpeg\n"
                "• Linux: sudo apt install ffmpeg\n\n"
                "O aplicativo não poderá processar vídeos sem o FFmpeg."
            )

    def _add_videos(self):
        """Open file dialog to add videos."""
        files = filedialog.askopenfilenames(
            title="Selecionar Vídeos",
            filetypes=self.SUPPORTED_FORMATS
        )
        if not files:
            return

        for f in files:
            # Skip duplicates
            if any(v.filepath == f for v in self.video_items):
                continue
            item = VideoItem(filepath=f)
            # Get video info in background
            info = FFmpegProcessor.get_video_info(f)
            item.width = info["width"]
            item.height = info["height"]
            item.duration = info["duration"]
            self.video_items.append(item)

        self._refresh_tree()

    def _remove_selected(self):
        """Remove selected video from queue."""
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self.video_items):
            self.video_items.pop(idx)
            self.selected_index = None
            self._refresh_tree()
            self._clear_info_panel()

    def _clear_queue(self):
        """Clear all videos from queue."""
        if self.video_items and messagebox.askyesno("Confirmar", "Limpar toda a fila?"):
            self.video_items.clear()
            self.selected_index = None
            self._refresh_tree()
            self._clear_info_panel()

    def _choose_output_dir(self):
        """Choose output directory."""
        d = filedialog.askdirectory(title="Escolher Pasta de Destino",
                                    initialdir=self.output_dir)
        if d:
            self.output_dir = d
            self.dir_label.configure(text=self._short_path(d))

    def _on_tree_select(self, event=None):
        """Handle video selection in tree."""
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self.video_items):
            self.selected_index = idx
            item = self.video_items[idx]
            self.info_name.configure(text=f"📄 {item.filename}")
            self.info_details.configure(
                text=f"Resolução: {item.resolution_str}  |  "
                     f"Duração: {item.duration_str}  |  "
                     f"Status: {item.status}"
            )
            self.caption_text.delete("1.0", tk.END)
            self.caption_text.insert("1.0", item.caption)

    def _on_caption_change(self, event=None):
        """Auto-save caption as user types."""
        if self.selected_index is not None and 0 <= self.selected_index < len(self.video_items):
            text = self.caption_text.get("1.0", tk.END).strip()
            self.video_items[self.selected_index].caption = text
            self._refresh_tree_item(self.selected_index)

    def _save_caption(self):
        """Explicitly save caption for selected video."""
        if self.selected_index is None:
            messagebox.showinfo("Info", "Selecione um vídeo primeiro.")
            return
        text = self.caption_text.get("1.0", tk.END).strip()
        self.video_items[self.selected_index].caption = text
        self._refresh_tree()

    def _apply_bulk_caption(self):
        """Apply bulk caption to all videos without a caption."""
        text = self.bulk_caption.get("1.0", tk.END).strip()
        if not text:
            return
        count = 0
        for item in self.video_items:
            if not item.caption.strip():
                item.caption = text
                count += 1
        self._refresh_tree()
        messagebox.showinfo("Concluído", f"Legenda aplicada a {count} vídeo(s).")

    # ─────────────────────────────────────────
    # Processing
    # ─────────────────────────────────────────

    def _start_processing(self):
        """Start batch processing in a background thread."""
        if self.is_processing:
            return
        if not self.video_items:
            messagebox.showinfo("Info", "Adicione vídeos à fila primeiro.")
            return

        pending = [v for v in self.video_items if v.status in ("Pendente", "Erro")]
        if not pending:
            messagebox.showinfo("Info", "Todos os vídeos já foram processados.")
            return

        if not FFmpegProcessor.check_ffmpeg():
            messagebox.showerror("Erro", "FFmpeg não encontrado. Instale antes de processar.")
            return

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        self.is_processing = True
        self.process_btn.configure(state="disabled")

        thread = threading.Thread(target=self._process_worker, args=(pending,), daemon=True)
        thread.start()

    def _process_worker(self, items: List[VideoItem]):
        """Worker thread for batch processing."""
        total = len(items)

        for i, item in enumerate(items):
            item.status = "Processando"
            self.root.after(0, self._refresh_tree)
            self.root.after(0, lambda idx=i, t=total:
                            self._update_progress_label(f"Processando {idx + 1}/{t}: {item.filename}"))
            self.root.after(0, lambda idx=i, t=total:
                            self.overall_label.configure(text=f"{idx}/{t} concluídos"))

            # Build output filename
            stem = Path(item.filepath).stem
            out_name = f"{stem}_tiktok.mp4"
            out_path = os.path.join(self.output_dir, out_name)

            # Avoid overwriting
            counter = 1
            while os.path.exists(out_path):
                out_name = f"{stem}_tiktok_{counter}.mp4"
                out_path = os.path.join(self.output_dir, out_name)
                counter += 1

            def progress_cb(pct, _item=item):
                self.root.after(0, lambda p=pct: self.progress_bar.configure(value=p))

            success = FFmpegProcessor.process_video(item, out_path, progress_cb)

            if success:
                item.status = "Concluído ✓"
            else:
                item.status = "Erro ✗"

            self.root.after(0, self._refresh_tree)

        self.root.after(0, lambda: self.progress_bar.configure(value=0))
        self.root.after(0, lambda: self._update_progress_label("Processamento concluído!"))
        self.root.after(0, lambda: self.overall_label.configure(text=f"{total}/{total} concluídos"))
        self.root.after(0, self._processing_done)

    def _processing_done(self):
        """Called when processing is finished."""
        self.is_processing = False
        self.process_btn.configure(state="normal")

        success = sum(1 for v in self.video_items if "Concluído" in v.status)
        errors = sum(1 for v in self.video_items if "Erro" in v.status)

        msg = f"Processamento finalizado!\n\n✅ {success} vídeo(s) processado(s) com sucesso"
        if errors:
            msg += f"\n❌ {errors} vídeo(s) com erro"
        msg += f"\n\n📁 Pasta de saída:\n{self.output_dir}"

        messagebox.showinfo("Concluído", msg)

    # ─────────────────────────────────────────
    # UI Helpers
    # ─────────────────────────────────────────

    def _refresh_tree(self):
        """Refresh the entire tree view."""
        self.tree.delete(*self.tree.get_children())
        for item in self.video_items:
            cap_preview = (item.caption[:35] + "…") if len(item.caption) > 35 else item.caption
            self.tree.insert("", tk.END, values=(
                item.filename,
                item.resolution_str,
                item.duration_str,
                cap_preview or "—",
                item.status
            ))
        self.video_count_label.configure(text=f"{len(self.video_items)} vídeo(s) na fila")

    def _refresh_tree_item(self, index: int):
        """Refresh a single row in the tree."""
        children = self.tree.get_children()
        if 0 <= index < len(children):
            item = self.video_items[index]
            cap_preview = (item.caption[:35] + "…") if len(item.caption) > 35 else item.caption
            self.tree.item(children[index], values=(
                item.filename,
                item.resolution_str,
                item.duration_str,
                cap_preview or "—",
                item.status
            ))

    def _clear_info_panel(self):
        """Reset the info/caption panel."""
        self.info_name.configure(text="Nenhum vídeo selecionado")
        self.info_details.configure(text="")
        self.caption_text.delete("1.0", tk.END)

    def _update_progress_label(self, text: str):
        """Update progress label text."""
        self.progress_label.configure(text=text)

    @staticmethod
    def _short_path(path: str, max_len: int = 45) -> str:
        """Shorten a path for display."""
        if len(path) <= max_len:
            return path
        return "…" + path[-(max_len - 1):]


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

def main():
    root = tk.Tk()

    # Try to set icon (won't crash if it fails)
    try:
        root.iconname("TikTok Processor")
    except Exception:
        pass

    app = TikTokProcessorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
