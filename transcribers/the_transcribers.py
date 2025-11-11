# -*- coding: utf-8 -*-
"""
The Transcribers - Audio to Text Conversion (v3)
- Engines: faster-whisper (offline), Google Web Speech (demo), OpenAI (cloud)
- GUI: add files/folder, denoise, export SRT, keep last N transcripts
- OpenAI Key dialog with Test

Usage (Linux/Mac):
  python the_transcribers_v3.py

Dependencies:
  sudo apt install ffmpeg
  pip install faster-whisper SpeechRecognition pydub openai
"""

import os
import json
import time
import threading
import subprocess
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ==================== small utilities ====================

def audio_duration_sec(wav_path: Path) -> float:
    """Intoarce durata WAV in secunde (folosind soundfile sau pydub)."""
    try:
        import soundfile as sf
        with sf.SoundFile(str(wav_path)) as f:
            return float(len(f)) / float(f.samplerate)
    except Exception:
        try:
            from pydub import AudioSegment
            return float(len(AudioSegment.from_wav(str(wav_path)))) / 1000.0
        except Exception:
            return 0.0

def split_wav_to_chunks(wav_path: Path, max_sec: int = 600, overlap_sec: float = 0.0):
    """
    Taie WAV-ul in bucati de max_sec (default 10 min), cu overlap optional.
    Returneaza lista [(chunk_path, start_sec, end_sec), ...].
    """
    from pydub import AudioSegment
    tmp_dir = wav_path.parent / ".tmp_transcriber"
    ensure_dir(tmp_dir)

    audio = AudioSegment.from_wav(str(wav_path))
    total_ms = len(audio)
    step_ms = int((max_sec - overlap_sec) * 1000)
    win_ms = int(max_sec * 1000)

    chunks = []
    i = 1
    for start_ms in range(0, total_ms, step_ms):
        end_ms = min(start_ms + win_ms, total_ms)
        piece = audio[start_ms:end_ms]
        out = tmp_dir / f"{sanitize_filename(wav_path.stem)}.part_{i:03d}.wav"
        piece.export(out, format="wav")
        chunks.append((out, start_ms/1000.0, end_ms/1000.0))
        i += 1
        if end_ms >= total_ms:
            break
    return chunks



def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p

def sanitize_filename(name: str) -> str:
    invalid = '<>:"/\\|?*'
    for ch in invalid:
        name = name.replace(ch, "_")
    return name.strip()

def validate_audio_file(path: Path):
    if not path.exists():
        return False, f"File not found: {path}"
    if not path.is_file():
        return False, f"Not a file: {path}"
    if path.suffix.lower() not in (".mp3", ".wav", ".m4a"):
        return False, f"Unsupported format: {path.suffix}"
    if path.stat().st_size < 1024:
        return False, f"File too small: {path.name}"
    return True, ""

def keep_last_n_transcripts(root: Path, n: int = 3) -> int:
    files = sorted(root.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for f in files[n:]:
        try:
            f.unlink(missing_ok=True)
            srt = f.with_suffix(".srt")
            if srt.exists():
                srt.unlink(missing_ok=True)
            removed += 1
        except Exception:
            pass
    return removed

def cleanup_temp_files(root: Path):
    for pat in ("*.tmp*.wav", "*.chunk_*.wav"):
        for f in root.rglob(pat):
            try: f.unlink(missing_ok=True)
            except Exception: pass

def run_ffmpeg_wav16k(src: Path, denoise: bool) -> Path:
    """
    Convert source to 16kHz mono WAV (temp file), optional denoise.
    """
    tmp_dir = src.parent / ".tmp_transcriber"
    ensure_dir(tmp_dir)
    out = tmp_dir / f"{sanitize_filename(src.stem)}_{int(time.time()*1000)}.wav"
    # conservative filters (no rnnoise model dependency)
    af = "highpass=f=100,lowpass=f=6000,dynaudnorm=f=150:g=15" if denoise else "anull"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src), "-ac", "1", "-ar", "16000",
        "-af", af if denoise else "anull",
        str(out)
    ]
    try:
        subprocess.run(cmd, check=True, text=True, capture_output=True, timeout=900)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg failed: {e.stderr or e}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg timeout (>15min)")
    if not out.exists():
        raise RuntimeError("FFmpeg did not create output")
    return out

def export_srt(segments, path: Path):
    def ts(sec: float):
        ms = int(round((sec - int(sec)) * 1000))
        s = int(sec) % 60
        m = (int(sec) // 60) % 60
        h = int(sec) // 3600
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    with path.open("w", encoding="utf-8") as f:
        idx = 1
        for s in segments:
            text = (s.get("text") or "").strip()
            if not text:
                continue
            f.write(f"{idx}\n{ts(s.get('start',0.0))} --> {ts(s.get('end',0.0))}\n{text}\n\n")
            idx += 1

# ==================== Engines ====================

class WhisperEngine:
    """
    faster-whisper (offline). Good accuracy, no quotas.
    """
    _cache = {}

    def __init__(self, model_name="small", compute_type="int8", log=None):
        self.log = log or (lambda *_: None)
        key = (model_name, compute_type)
        if key in WhisperEngine._cache:
            self.model = WhisperEngine._cache[key]
            return
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError("Missing 'faster-whisper'. Install: pip install faster-whisper")
        self.log(f"[Whisper] Loading model: {model_name} ({compute_type}) ...")
        try:
            self.model = WhisperModel(model_name, compute_type=compute_type)
        except Exception as e:
            raise RuntimeError(f"Whisper load error: {e}")
        WhisperEngine._cache[key] = self.model
        self.log("[Whisper] Ready.")

    def transcribe(self, wav_path: Path):
        try:
            segs, info = self.model.transcribe(
                str(wav_path),
                language=None,
                vad_filter=True,
                word_timestamps=False,
                condition_on_previous_text=False,
                beam_size=5, best_of=5, temperature=0.0, patience=0.2,
                no_speech_threshold=0.45
            )
            segments = [{
                "start": float(s.start or 0.0),
                "end": float(s.end or 0.0),
                "text": (s.text or "").strip()
            } for s in segs]
            text = " ".join(s["text"] for s in segments).strip()
            meta = {
                "language": getattr(info, "language", "auto"),
                "language_probability": float(getattr(info, "language_probability", 0.0)),
                "duration_sec": float(getattr(info, "duration", 0.0))
            }
            return {"text": text, "segments": segments, "metadata": meta}
        except Exception as e:
            raise RuntimeError(f"Whisper transcription failed: {e}")

class GoogleEngine:
    """
    Google Web Speech (demo). Limited quota; for quick tests only.
    """
    def __init__(self, log=None, max_retries=3):
        self.log = log or (lambda *_: None)
        self.max_retries = max_retries
        try:
            import speech_recognition as sr
            from pydub import AudioSegment  # noqa
        except ImportError:
            raise RuntimeError("Missing deps. Install: pip install SpeechRecognition pydub")
        self.sr = sr
        self.AudioSegment = AudioSegment
        self.log("[Google] FREE tier (rate limited)")

    def _chunk(self, audio_path: Path, start: float, end: float, attempt=1):
        r = self.sr.Recognizer()
        with self.sr.AudioFile(str(audio_path)) as source:
            data = r.record(source)
        try:
            text = r.recognize_google(data, language="ro-RO")
            return text.strip(), True
        except self.sr.UnknownValueError:
            return "", False
        except self.sr.RequestError as e:
            msg = str(e).lower()
            if any(k in msg for k in ("quota", "limit", "429")):
                raise RuntimeError("Google API rate limit. Use Whisper/OpenAI.")
            if attempt < self.max_retries:
                time.sleep(2 * (2 ** (attempt - 1)))
                return self._chunk(audio_path, start, end, attempt + 1)
            raise RuntimeError(f"Google API failed: {e}")

    def transcribe(self, wav_path: Path):
        audio = self.AudioSegment.from_wav(str(wav_path))
        dur = len(audio) / 1000.0
        chunk_ms = 20000 if dur < 60 else (25000 if dur < 300 else 30000)
        segs, texts = [], []
        total = (len(audio) + chunk_ms - 1) // chunk_ms
        for i, off in enumerate(range(0, len(audio), chunk_ms), 1):
            piece = audio[off:off+chunk_ms]
            tmp = wav_path.with_suffix(f".chunk_{i:03d}.wav")
            try:
                piece.export(tmp, format="wav")
                s = off/1000.0
                e = (off+len(piece))/1000.0
                self.log(f"  [Google] {i}/{total} {s:.0f}s-{e:.0f}s")
                t, ok = self._chunk(tmp, s, e)
                if t:
                    segs.append({"start": s, "end": e, "text": t})
                    texts.append(t)
            finally:
                try: tmp.unlink()
                except Exception: pass
        full = " ".join(texts).strip()
        if not full:
            raise RuntimeError("No speech detected.")
        return full, segs, {"language": "ro", "language_probability": 1.0, "duration_sec": dur}

class OpenAIEngine:
    """
    OpenAI STT (cloud).
    - gpt-4o-mini-transcribe  -> response_format='json' (fara segmente)
    - whisper-1               -> response_format='verbose_json' (cu segmente)
    Daca fisierul e prea mare/lung, il sparge automat in bucati.
    """
    # limite aproximative (sigur sub plafonul API-ului)
    MODEL_HARD_SEC = {
        "whisper-1": 1400,                 # ~23 min
        "gpt-4o-mini-transcribe": 6000     # punem mare; oricum limitam si pe bytes
    }
    MAX_REQUEST_BYTES = 20 * 1024 * 1024   # ~20MB per request (safe)
    DEFAULT_CHUNK_SEC = 600                # 10 minute per chunk

    def __init__(self, model="gpt-4o-mini-transcribe", api_key=None, log=None):
        self.log = log or (lambda *_: None)
        try:
            from openai import OpenAI  # noqa: F401
        except Exception:
            raise RuntimeError("Lipseste 'openai'. Instaleaza: pip install openai")

        key = (api_key or os.getenv("OPENAI_API_KEY") or "").strip()
        if not key:
            raise RuntimeError("OpenAI API key lipsa. Foloseste butonul «OpenAI Key…».")

        from openai import OpenAI
        self.client = OpenAI(api_key=key)
        self.model = model
        self._verbose = self.model.startswith("whisper")

    def _call_api_once(self, wav_path: Path, start_offset: float = 0.0):
        """Trimite un singur chunk catre API si intoarce (text, segmente) relative la chunk."""
        fmt = "verbose_json" if self._verbose else "json"
        with open(wav_path, "rb") as f:
            resp = self.client.audio.transcriptions.create(
                model=self.model,
                file=f,
                response_format=fmt,
            )

        # extrage text + segmente relative la chunk
        if hasattr(resp, "text"):
            text = (resp.text or "").strip()
        elif isinstance(resp, dict):
            text = (resp.get("text") or "").strip()
        else:
            text = ""

        segments = []
        if fmt == "verbose_json":
            raw = getattr(resp, "segments", None) or (resp.get("segments") if isinstance(resp, dict) else None)
            if raw:
                for s in raw:
                    segments.append({
                        "start": float(s.get("start", 0.0)),
                        "end": float(s.get("end", 0.0)),
                        "text": (s.get("text", "") or "").strip()
                    })
            else:
                segments = [{"start": 0.0, "end": 0.0, "text": text}]
        else:
            # fara segmente -> facem un bloc cat chunk-ul
            dur = audio_duration_sec(wav_path)
            segments = [{"start": 0.0, "end": float(dur), "text": text}]

        # deplaseaza segmentele la timpul global (adaugam offset)
        for s in segments:
            s["start"] += start_offset
            s["end"] += start_offset

        return text, segments

    def transcribe(self, wav_path: Path):
        # calculeaza durata si bitrate pentru a decide chunking
        dur = audio_duration_sec(wav_path)
        size = wav_path.stat().st_size
        bytes_per_sec = (size / dur) if dur > 0 else (32000.0)  # ~32kB/s la 16kHz PCM

        hard_sec = self.MODEL_HARD_SEC.get(self.model, 3600)
        # cat putem trimite sigur pe request tinand cont de bytes
        safe_by_bytes = max(60, int((self.MAX_REQUEST_BYTES * 0.9) / bytes_per_sec))
        per_chunk_sec = max(60, min(self.DEFAULT_CHUNK_SEC, int(hard_sec * 0.7), safe_by_bytes))

        need_chunk = (dur > per_chunk_sec) or (size > self.MAX_REQUEST_BYTES)

        if not need_chunk:
            # simplu: un singur request
            text, segments = self._call_api_once(wav_path, start_offset=0.0)
            meta = {"language": "auto", "language_probability": 1.0 if text else 0.0, "duration_sec": dur}
            return text, segments, meta

        # chunking
        self.log(f"[OpenAI] File prea mare – sparg in bucati de ~{per_chunk_sec//60} min...")
        parts = split_wav_to_chunks(wav_path, max_sec=per_chunk_sec, overlap_sec=0.0)

        all_text = []
        all_segments = []
        for i, (chunk, s, e) in enumerate(parts, 1):
            self.log(f"  [Chunk {i}/{len(parts)}] {s:.0f}s–{e:.0f}s ...")
            try:
                t, segs = self._call_api_once(chunk, start_offset=s)
                if t:
                    all_text.append(t)
                all_segments.extend(segs)
            finally:
                try:
                    chunk.unlink(missing_ok=True)
                except Exception:
                    pass

        meta = {"language": "auto", "language_probability": 1.0 if all_text else 0.0, "duration_sec": dur}
        return " ".join(all_text).strip(), all_segments, meta


# ==================== GUI app ====================

class TranscribersApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("The Transcribers - Audio to Text Conversion")
        self.geometry("1000x680")
        self.configure(bg="#10131a")

        self.audio_files: list[tuple[Path, Path|None]] = []
        self.stop_processing = False
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()

        self.engine_var = tk.StringVar(value="whisper")
        self.model_var = tk.StringVar(value=os.getenv("WHISPER_MODEL", "small"))
        self.compute_var = tk.StringVar(value=os.getenv("COMPUTE_TYPE", "int8"))
        self.denoise_var = tk.BooleanVar(value=True)
        self.export_srt_var = tk.BooleanVar(value=True)
        self.keep_last_var = tk.IntVar(value=3)
        self.output_dir = tk.StringVar(value=str((Path.cwd() / "Received" / "transcripts").resolve()))

        self._build_interface()
        self._check_base_deps()

    # ---------- UI ----------

    def _build_interface(self):
        pad = {"padx": 8, "pady": 6}

        header = tk.Frame(self, bg="#10131a")
        header.pack(fill="x", **pad)

        tk.Button(header, text="Add MP3 Files...", command=self._add_files,
                  bg="#243145", fg="white").pack(side="left", padx=3)
        tk.Button(header, text="Add Folder...", command=self._add_folder,
                  bg="#243145", fg="white").pack(side="left", padx=3)
        tk.Button(header, text="Clear List", command=self._clear_files,
                  bg="#243145", fg="white").pack(side="left", padx=3)

        tk.Label(header, text="Engine:", bg="#10131a", fg="#E0E6ED").pack(side="left", padx=(16,4))
        eng = ttk.Combobox(header, textvariable=self.engine_var,
                           values=["whisper", "google", "openai"], state="readonly", width=10)
        eng.pack(side="left")
        eng.bind("<<ComboboxSelected>>", self._on_engine_change)

        tk.Label(header, text="Model:", bg="#10131a", fg="#E0E6ED").pack(side="left", padx=(12,4))
        self.model_combo = ttk.Combobox(header, textvariable=self.model_var, state="readonly",
                                        values=["tiny","base","small","medium","large-v2","large-v3"], width=16)
        self.model_combo.pack(side="left")

        tk.Button(header, text="OpenAI Key...", command=self._open_openai_key_dialog,
                  bg="#243145", fg="white").pack(side="left", padx=6)

        options = tk.Frame(self, bg="#10131a")
        options.pack(fill="x", **pad)

        tk.Checkbutton(options, text="Denoise Audio", variable=self.denoise_var,
                       bg="#10131a", fg="#E0E6ED", selectcolor="#1a2233").pack(side="left")
        tk.Checkbutton(options, text="Export SRT Subtitles", variable=self.export_srt_var,
                       bg="#10131a", fg="#E0E6ED", selectcolor="#1a2233").pack(side="left", padx=(16,0))

        tk.Label(options, text="Keep last:", bg="#10131a", fg="#E0E6ED").pack(side="left", padx=(16,4))
        tk.Entry(options, textvariable=self.keep_last_var, width=4,
                 bg="#182033", fg="white", insertbackground="white").pack(side="left")

        tk.Label(options, text="Output:", bg="#10131a", fg="#E0E6ED").pack(side="left", padx=(16,4))
        tk.Entry(options, textvariable=self.output_dir, width=42,
                 bg="#182033", fg="white", insertbackground="white").pack(side="left", padx=(0,4))
        tk.Button(options, text="Browse...", command=self._choose_output,
                  bg="#243145", fg="white").pack(side="left")

        content = tk.Frame(self, bg="#10131a")
        content.pack(fill="both", expand=True, **pad)

        left = tk.Frame(content, bg="#10131a"); left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="Audio Files", bg="#10131a", fg="#E0E6ED",
                 font=("Arial", 10, "bold")).pack(anchor="w")
        self.files_list = tk.Listbox(left, bg="#0f1524", fg="white", font=("Courier", 9))
        self.files_list.pack(fill="both", expand=True)
        self.files_count = tk.Label(left, text="0 files", bg="#10131a", fg="#8aa")
        self.files_count.pack(anchor="w", pady=(4,0))

        right = tk.Frame(content, bg="#10131a"); right.pack(side="right", fill="both", expand=True)
        tk.Label(right, text="Processing Log", bg="#10131a", fg="#E0E6ED",
                 font=("Arial", 10, "bold")).pack(anchor="w")
        self.log_box = tk.Text(right, height=20, bg="#0f1524", fg="#dfe6f0",
                               insertbackground="white", font=("Courier", 9))
        self.log_box.pack(fill="both", expand=True)

        footer = tk.Frame(self, bg="#10131a"); footer.pack(fill="x", **pad)
        self.progress = ttk.Progressbar(footer, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(0,10))
        tk.Button(footer, text="START", command=self._start_processing,
                  bg="#1E90FF", fg="white", width=12).pack(side="left", padx=4)
        tk.Button(footer, text="STOP", command=self._stop_processing,
                  bg="#FF4444", fg="white", width=12).pack(side="left", padx=4)

    def _log(self, *msgs):
        self.log_box.insert(tk.END, " ".join(str(m) for m in msgs) + "\n")
        self.log_box.see(tk.END)
        self.update_idletasks()

    # ---------- deps / engine change ----------

    def _check_base_deps(self):
        miss = []
        try:
            subprocess.run(["ffmpeg","-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        except Exception:
            miss.append("ffmpeg (sudo apt install ffmpeg)")
        try:
            import faster_whisper  # noqa
        except Exception:
            miss.append("faster-whisper (pip install faster-whisper)")
        if miss:
            messagebox.showwarning("Dependencies", "Missing:\n\n" + "\n".join("• "+m for m in miss))

    def _on_engine_change(self, _evt=None):
        eng = self.engine_var.get()
        if eng == "whisper":
            self.model_combo["values"] = ["tiny","base","small","medium","large-v2","large-v3"]
            if self.model_var.get() not in self.model_combo["values"]:
                self.model_var.set("small")
            self.model_combo["state"] = "readonly"
        elif eng == "google":
            self.model_combo["values"] = ["(n/a)"]
            self.model_var.set("(n/a)")
            self.model_combo["state"] = "disabled"
            messagebox.showinfo("Google Web Speech",
                                "Free demo API, limita ~50 requests/zi. Pentru proiect foloseste Whisper/OpenAI.")
        else:  # openai
            self.model_combo["values"] = ["gpt-4o-mini-transcribe", "whisper-1"]
            if self.model_var.get() not in self.model_combo["values"]:
                self.model_var.set("gpt-4o-mini-transcribe")
            self.model_combo["state"] = "readonly"

    # ---------- file ops ----------

    def _add_files(self):
        paths = filedialog.askopenfilenames(title="Select audio files",
                                            filetypes=[("Audio", "*.mp3 *.wav *.m4a"), ("All","*.*")])
        bad = 0
        for p in paths:
            ok, err = validate_audio_file(Path(p))
            if ok:
                self.audio_files.append((Path(p), None))
                self.files_list.insert(tk.END, Path(p).name)
            else:
                bad += 1; self._log("[SKIPPED]", err)
        if bad:
            messagebox.showwarning("Warning", f"Skipped {bad} invalid file(s).")
        self.files_count.config(text=f"{len(self.audio_files)} files")

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select folder with audio")
        if not folder: return
        base = Path(folder)
        found = [p for p in base.rglob("*") if p.suffix.lower() in (".mp3",".wav",".m4a")]
        if not found:
            messagebox.showinfo("Info", "No audio files found in folder."); return
        cnt = 0
        for p in found:
            ok, _ = validate_audio_file(p)
            if ok:
                self.audio_files.append((p, base))
                self.files_list.insert(tk.END, str(p.relative_to(base)))
                cnt += 1
        self.files_count.config(text=f"{cnt} valid files")

    def _clear_files(self):
        self.audio_files.clear()
        self.files_list.delete(0, tk.END)
        self.files_count.config(text="0 files")

    def _choose_output(self):
        folder = filedialog.askdirectory(title="Output folder", initialdir=self.output_dir.get())
        if folder:
            self.output_dir.set(folder)

    # ---------- OpenAI key dialog ----------

    def _open_openai_key_dialog(self):
        win = tk.Toplevel(self); win.title("Set OpenAI API Key"); win.configure(bg="#10131a")
        tk.Label(win, text="OpenAI API Key:", bg="#10131a", fg="#E0E6ED").pack(anchor="w", padx=12, pady=(12,6))
        var = tk.StringVar(value=self.openai_key)
        ent = tk.Entry(win, textvariable=var, width=60, bg="#182033", fg="white", insertbackground="white", show="•")
        ent.pack(padx=12, pady=4); ent.focus_set()

        def test_key():
            key = var.get().strip()
            if not key:
                messagebox.showwarning("Warning", "Key is empty."); return
            try:
                from openai import OpenAI
                client = OpenAI(api_key=key)
                _ = client.models.list()
                messagebox.showinfo("OK", "Key valid (auth OK).")
            except Exception as e:
                messagebox.showerror("Invalid", f"Key invalid sau proiect fara billing:\n{e}")

        def save():
            k = var.get().strip()
            if not k:
                messagebox.showwarning("Warning", "Key cannot be empty."); return
            self.openai_key = k
            messagebox.showinfo("OK", "Key set in memory (nu se salveaza pe disk).")
            win.destroy()

        row = tk.Frame(win, bg="#10131a"); row.pack(fill="x", pady=10)
        tk.Button(row, text="Test", command=test_key, bg="#243145", fg="white").pack(side="left", padx=8)
        tk.Button(row, text="Save", command=save, bg="#1E90FF", fg="white").pack(side="right", padx=8)
        tk.Button(row, text="Close", command=win.destroy, bg="#243145", fg="white").pack(side="right")

    # ---------- processing ----------

    def _start_processing(self):
        if not self.audio_files:
            messagebox.showwarning("Warning", "No files selected."); return
        ensure_dir(Path(self.output_dir.get()))
        self.stop_processing = False
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.audio_files)
        threading.Thread(target=self._worker_process, daemon=True).start()

    def _stop_processing(self):
        self.stop_processing = True

    def _get_output_path(self, src: Path, base: Path|None, suffix: str) -> Path:
        root = Path(self.output_dir.get())
        if base is None:
            return ensure_dir(root) / sanitize_filename(src.stem + suffix)
        rel = src.relative_to(base).with_suffix(suffix)
        dst = root / rel
        ensure_dir(dst.parent)
        return dst

    def _worker_process(self):
        # pick engine
        try:
            if self.engine_var.get() == "whisper":
                engine = WhisperEngine(self.model_var.get(), self.compute_var.get(), log=self._log)
            elif self.engine_var.get() == "google":
                engine = GoogleEngine(log=self._log)
            else:
                engine = OpenAIEngine(model=self.model_var.get(), api_key=self.openai_key, log=self._log)
        except Exception as e:
            self._log("[ERROR] Engine init:", e); return

        ok, err = 0, 0
        total_audio = 0.0
        t0 = time.time()

        for idx, (src, base) in enumerate(self.audio_files, 1):
            if self.stop_processing: break
            wav = None
            try:
                self._log(f"\n[{idx}/{len(self.audio_files)}] Processing:", src.name)
                self._log("├─ Audio preprocessing ...")
                wav = run_ffmpeg_wav16k(src, denoise=bool(self.denoise_var.get()))

                self._log(f"├─ Transcribing [{self.engine_var.get().upper()}] ...")
                full, segments, meta = engine.transcribe(wav)
                dur = float(meta.get("duration_sec", 0.0))
                total_audio += dur

                payload = {
                    "version": "1.0",
                    "timestamp": now_iso(),
                    "source_file": src.name,
                    "duration_sec": dur,
                    "language": meta.get("language", "auto"),
                    "language_confidence": float(meta.get("language_probability", 0.0)),
                    "text": full,
                    "segments": segments,
                    "metadata": {
                        "engine": self.engine_var.get(),
                        "model": self.model_var.get(),
                        "denoise": bool(self.denoise_var.get()),
                        "processed_at": datetime.now().isoformat()
                    }
                }

                json_path = self._get_output_path(src, base, ".json")
                json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                self._log("├─ Saved:", json_path.name)

                if self.export_srt_var.get():
                    srt_path = self._get_output_path(src, base, ".srt")
                    export_srt(segments, srt_path)
                    self._log("└─ SRT export:", srt_path.name)

                ok += 1
                self._log("✓ DONE")
            except Exception as e:
                err += 1
                self._log("✗ ERROR:", e)
            finally:
                if wav and wav.exists():
                    try: wav.unlink()
                    except Exception: pass
                self.progress["value"] = idx
                self.update_idletasks()

        # cleanup
        try:
            cleanup_temp_files(Path(self.output_dir.get()))
            removed = keep_last_n_transcripts(Path(self.output_dir.get()), n=int(self.keep_last_var.get()))
            if removed:
                self._log(f"[Cleanup] Deleted {removed} old transcripts")
        except Exception as e:
            self._log("[Cleanup warning]", e)

        self._log("\n" + "="*54)
        self._log("BATCH COMPLETE")
        self._log(f"  Success: {ok} / Failed: {err}")
        self._log(f"  Total audio: {total_audio:.1f}s ({total_audio/60:.1f}m)")
        self._log(f"  Processing time: {time.time()-t0:.1f}s")
        self._log(f"  Output: {self.output_dir.get()}")
        self._log("="*54)

# -------------------- main --------------------

if __name__ == "__main__":
    app = TranscribersApp()
    app.mainloop()
