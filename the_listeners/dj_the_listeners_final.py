# -*- coding: utf-8 -*-
"""
DJ Listener V2 FINAL - Interfață Grafică PyQt6
Obiectiv: Înregistrare Multi-Canal WAV (Self/Others) și salvare Configurație JSON.
"""
import sys
import os
import time
import datetime
from pathlib import Path
import json  # NOU: Pentru salvarea și încărcarea configurației JSON
from typing import Optional

# --- DEPENDENȚE AUDIO ---
import pyaudio
import wave

# --- DEPENDENȚE GUI ---
from PyQt6.QtCore import QThread, pyqtSignal

from .device_helpers import resolve_device_params
# ----------------------------------------------------
# 1. CONSTANTE ȘI CĂI
# ----------------------------------------------------

# MODIFICARE: Nu mai e nevoie de FFmpeg/pydub
RECORDINGS_DIR = Path.cwd() / "recordings_wav"  # Toate fișierele finale (WAV) aici
CONFIG_FILE = Path.cwd() / "listener_config.json"  # Fișierul de configurare salvat

# Constante Audio
CHUNK = 1024
FORMAT = pyaudio.paInt16
RATE = 44100
RECORD_SECONDS = 60  # Durata ciclului de monitorizare


# ----------------------------------------------------
# 2. CLASA WORKER PENTRU ÎNREGISTRARE ÎN FUNDAL
# ----------------------------------------------------

class RecordingWorker(QThread):
    finished_cycle = pyqtSignal(str, str)  # Emite căile fișierelor WAV (Self, Others)
    progress_update = pyqtSignal(int)
    log_message = pyqtSignal(str)

    def __init__(self, mic_id: int, speaker_id: Optional[int], duration: int):
        super().__init__()
        self.mic_id = mic_id
        self.speaker_id = speaker_id
        self.duration = duration
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        self.log_message.emit("--- MONITORIZARE CONTINUĂ PORNITĂ ---")
        p = pyaudio.PyAudio()

        try:
            while self._is_running:
                mic_stream = None
                speaker_stream = None
                speaker_channels = 0

                try:
                    self.log_message.emit(f"\n🎧 NOU CICLU START. Durată: {self.duration}s")

                    # 1. Configurare Microfon (CH1 - SELF)
                    mic_info = p.get_device_info_by_index(self.mic_id)
                    mic_stream = p.open(format=FORMAT, channels=1, rate=RATE,
                                        input=True, input_device_index=self.mic_id,
                                        frames_per_buffer=CHUNK)
                    self.log_message.emit(f"CH1 (Self/Microfon): '{mic_info['name']}' - OK.")

                    # 2. Configurare Boxe/Loopback (CH2 - OTHERS) cu Fallback
                    if self.speaker_id is not None:
                        speaker_info = p.get_device_info_by_index(self.speaker_id)

                        try:  # Try 2 Channels
                            speaker_channels = 2
                            speaker_stream = p.open(
                                format=FORMAT,
                                channels=speaker_channels,
                                rate=RATE,
                                input=True,
                                input_device_index=self.speaker_id,
                                frames_per_buffer=CHUNK,
                            )
                            self.log_message.emit(
                                f"CH2 (Others/Boxe): '{speaker_info['name']}' - 2 canale (Stereo) OK."
                            )
                        except Exception:
                            try:  # Try 1 Channel
                                speaker_channels = 1
                                speaker_stream = p.open(
                                    format=FORMAT,
                                    channels=speaker_channels,
                                    rate=RATE,
                                    input=True,
                                    input_device_index=self.speaker_id,
                                    frames_per_buffer=CHUNK,
                                )
                                self.log_message.emit(
                                    f"CH2 (Others/Boxe): '{speaker_info['name']}' - 1 canal (Mono Fallback) OK."
                                )
                            except Exception as e_mono:
                                self.log_message.emit(
                                    f"❌ EROARE CRITICĂ CH2: Eșec: {e_mono}. Canalul NU va fi înregistrat în acest ciclu."
                                )
                                speaker_stream = None
                                speaker_channels = 0
                    else:
                        self.log_message.emit("CH2 (Others/Boxe): dezactivat (nu s-a găsit dispozitiv de loopback).")

                    # 3. Citirea și colectarea datelor
                    mic_frames = []
                    speaker_frames = []
                    num_chunks = int(RATE / CHUNK * self.duration)

                    self.log_message.emit("Înregistrare în curs...")
                    for i in range(num_chunks):
                        if not self._is_running:
                            break

                        # Citire CH1 (SELF)
                        mic_frames.append(mic_stream.read(CHUNK, exception_on_overflow=False))

                        # Citire CH2 (OTHERS)
                        if speaker_stream:
                            speaker_frames.append(speaker_stream.read(CHUNK, exception_on_overflow=False))

                        self.progress_update.emit(int((i + 1) / num_chunks * 100))

                    if not self._is_running:
                        break

                    self.log_message.emit("Ciclu înregistrare brută finalizat. Salvare WAV...")

                    # 4. Salvarea fișierelor WAV (DIRECT ÎN RECORDINGS_DIR)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

                    os.makedirs(RECORDINGS_DIR, exist_ok=True)

                    # NOU: Numele fișierelor reflectă canalele SELF/OTHERS
                    self_wav_path = os.path.join(RECORDINGS_DIR, f"self_{timestamp}.wav")
                    others_wav_path = os.path.join(RECORDINGS_DIR, f"others_{timestamp}.wav")

                    # Salvează SELF (Microfon)
                    with wave.open(self_wav_path, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(p.get_sample_size(FORMAT))
                        wf.setframerate(RATE)
                        wf.writeframes(b''.join(mic_frames))
                    self.log_message.emit(f"   💾 SELF (WAV) salvat: {Path(self_wav_path).name}")

                    # Salvează OTHERS (Boxe)
                    if speaker_stream and speaker_frames:
                        with wave.open(others_wav_path, 'wb') as wf:
                            wf.setnchannels(speaker_channels)
                            wf.setsampwidth(p.get_sample_size(FORMAT))
                            wf.setframerate(RATE)
                            wf.writeframes(b''.join(speaker_frames))
                        self.log_message.emit(f"   💾 OTHERS (WAV) salvat: {Path(others_wav_path).name}")
                    else:
                        others_wav_path = None
                        self.log_message.emit("   ❌ OTHERS nu a putut fi salvat.")

                    # Emite semnalul de finalizare cu căile fișierelor
                    self.finished_cycle.emit(self_wav_path, others_wav_path if others_wav_path else "")

                except Exception as e:
                    self.log_message.emit(f"❌ EROARE ÎN TIMPUL CICLULUI: {e}")

                finally:
                    # Închidere stream-uri (esențial înainte de a reîncepe bucla)
                    if mic_stream:
                        mic_stream.stop_stream()
                        mic_stream.close()
                    if speaker_stream:
                        speaker_stream.stop_stream()
                        speaker_stream.close()

        except Exception as e:
            self.log_message.emit(f"❌ EROARE FATALĂ ÎN THREAD: {e}")

        finally:
            p.terminate()
            self.log_message.emit("--- MONITORIZARE OPRITĂ ---")


def create_worker_with_default_devices(duration: int = RECORD_SECONDS) -> "RecordingWorker":
    """
    Convenience factory that instantiates `RecordingWorker` using the default
    microphone and speaker/loopback devices detected on the host machine.
    """
    params = resolve_device_params(duration)
    return RecordingWorker(
        mic_id=params["mic_id"],
        speaker_id=params.get("speaker_id"),
        duration=params["duration"],
    )
