# -*- coding: utf-8 -*-
"""
DJ GUI Recorder - Interfață Grafică PyQt6 pentru Înregistrarea Multi-Canal
# Requires Python 3.11
# System dependency: ffmpeg must be installed and in PATH
"""
import sys
import os
import threading
import time
import datetime
from pathlib import Path
import shutil  # Adăugat pentru a muta fișierele

# --- DEPENDENȚE AUDIO ---
import pyaudio
import wave
# Am ELIMINAT importul pydub de aici. Îl vom importa în funcția de conversie.

# --- DEPENDENȚE GUI ---
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QLineEdit, QProgressBar, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal as pyqtSignal, QTimer


# ----------------------------------------------------
# 0. PREGĂTIREA CĂII FFmpeg PENTRU DISTRIBUIRE
# ----------------------------------------------------

def setup_ffmpeg_path():
    """
    Setează calea către executabilul FFmpeg pentru pydub.
    Această funcție este esențială pentru a face aplicația funcțională
    după împachetare (bundling) cu PyInstaller.
    """
    # Trebuie să importăm pydub aici temporar pentru a accesa AudioSegment
    try:
        from pydub import AudioSegment
    except ImportError:
        return "Avertisment: pydub nu poate fi importat, nu se poate seta calea FFmpeg."

    try:
        # Detectează dacă rulează ca executabil împachetat (frozen)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Calea internă în pachetul PyInstaller
            application_path = sys._MEIPASS
            # Presupunem că binarul FFmpeg se află în 'bin/ffmpeg.exe'
            ffmpeg_path = os.path.join(application_path, "bin", "ffmpeg.exe")
            # Setarea explicită a căii pentru pydub
            AudioSegment.converter = ffmpeg_path
            return f"Cale FFmpeg setată (Bundled): {ffmpeg_path}"
        else:
            # Rulare normală în mediul de dezvoltare. pydub va folosi PATH-ul sistemului.
            return "Cale FFmpeg lăsată la setarea implicită (PATH)."
    except Exception as e:
        return f"Avertisment: Eroare la setarea căii FFmpeg: {e}"


# ----------------------------------------------------
# 1. CONSTANTE DE CONFIGURARE
# ----------------------------------------------------

# MODIFICARE: Folosim calea absolută a directorului de lucru
RECORDINGS_DIR = Path.cwd() / "recordings_gui"
WAV_BACKUP_DIR = Path.cwd() / "backup_wav_gui"  # NOU DIRECTOR DE BACKUP
CHUNK = 1024
FORMAT = pyaudio.paInt16
RATE = 44100
RECORD_SECONDS = 20  # 10 minute pentru ciclul continuu


# ----------------------------------------------------
# 2. CLASA WORKER PENTRU ÎNREGISTRARE ÎN FUNDAL
# ----------------------------------------------------

class RecordingWorker(QThread):
    finished_cycle = pyqtSignal(str, str)  # Emite după fiecare ciclu WAV -> MP3
    progress_update = pyqtSignal(int)
    log_message = pyqtSignal(str)

    def __init__(self, mic_id: int, speaker_id: int, duration: int):
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

                    # 1. Configurare Microfon (CH1)
                    mic_info = p.get_device_info_by_index(self.mic_id)
                    mic_stream = p.open(format=FORMAT, channels=1, rate=RATE,
                                        input=True, input_device_index=self.mic_id,
                                        frames_per_buffer=CHUNK)
                    self.log_message.emit(f"CH1 (Microfon): '{mic_info['name']}' - OK.")

                    # 2. Configurare Boxe/Loopback (CH2) cu Fallback (2 Canale -> 1 Canal)
                    speaker_info = p.get_device_info_by_index(self.speaker_id)

                    try:  # Try 2 Channels
                        speaker_channels = 2
                        speaker_stream = p.open(format=FORMAT, channels=speaker_channels,
                                                rate=RATE, input=True, input_device_index=self.speaker_id,
                                                frames_per_buffer=CHUNK)
                        self.log_message.emit(f"CH2 (Boxe): '{speaker_info['name']}' - 2 canale (Stereo) OK.")
                    except Exception:
                        try:  # Try 1 Channel
                            speaker_channels = 1
                            speaker_stream = p.open(format=FORMAT, channels=speaker_channels,
                                                    rate=RATE, input=True, input_device_index=self.speaker_id,
                                                    frames_per_buffer=CHUNK)
                            self.log_message.emit(f"CH2 (Boxe): '{speaker_info['name']}' - 1 canal (Mono Fallback) OK.")
                        except Exception as e_mono:
                            self.log_message.emit(
                                f"❌ EROARE CRITICĂ CH2: Eșec: {e_mono}. Canalul NU va fi înregistrat în acest ciclu.")
                            speaker_stream = None
                            speaker_channels = 0

                    # 3. Citirea și colectarea datelor
                    mic_frames = []
                    speaker_frames = []
                    num_chunks = int(RATE / CHUNK * self.duration)

                    self.log_message.emit("Înregistrare în curs...")
                    for i in range(num_chunks):
                        if not self._is_running:
                            break

                        # Citire CH1 (Microfon)
                        mic_frames.append(mic_stream.read(CHUNK, exception_on_overflow=False))

                        # Citire CH2 (Boxe)
                        if speaker_stream:
                            speaker_frames.append(speaker_stream.read(CHUNK, exception_on_overflow=False))

                        self.progress_update.emit(int((i + 1) / num_chunks * 100))

                    if not self._is_running:  # Ieșire imediată dacă s-a apăsat STOP
                        break

                    self.log_message.emit("Ciclu înregistrare brută finalizat. Salvare...")

                    # 4. Salvarea fișierelor WAV
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

                    # CREARE DIRECTOARE OBLIGATORIE AICI (folosind calea absolută)
                    os.makedirs(RECORDINGS_DIR, exist_ok=True)
                    os.makedirs(WAV_BACKUP_DIR, exist_ok=True)  # CREARE DIRECTOR BACKUP

                    mic_wav_path = os.path.join(WAV_BACKUP_DIR, f"ch1_mic_{timestamp}.wav")
                    speaker_wav_path = os.path.join(WAV_BACKUP_DIR, f"ch2_speakers_{timestamp}.wav")

                    # Salvează Microfonul (Channel 1)
                    with wave.open(mic_wav_path, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(p.get_sample_size(FORMAT))
                        wf.setframerate(RATE)
                        wf.writeframes(b''.join(mic_frames))
                    self.log_message.emit(f"   💾 CH1 (WAV) salvat în backup.")

                    # Salvează Boxele (Channel 2)
                    if speaker_stream and speaker_frames:
                        with wave.open(speaker_wav_path, 'wb') as wf:
                            wf.setnchannels(speaker_channels)
                            wf.setsampwidth(p.get_sample_size(FORMAT))
                            wf.setframerate(RATE)
                            wf.writeframes(b''.join(speaker_frames))
                        self.log_message.emit(f"   💾 CH2 (WAV) salvat în backup.")
                    else:
                        speaker_wav_path = None
                        self.log_message.emit("   ❌ CH2 nu a putut fi salvat.")

                    # Emite semnalul de finalizare cu căile fișierelor
                    self.finished_cycle.emit(mic_wav_path, speaker_wav_path if speaker_wav_path else "")

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


# ----------------------------------------------------
# 3. CLASA PRINCIPALĂ APLICAȚIEI GUI
# ----------------------------------------------------

class DJGUIRecorder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DJ BlueAI Multi-Channel Recorder (PySide6)")
        self.setGeometry(100, 100, 700, 500)

        # PyAudio este inițializat o singură dată
        self.pyaudio_instance = pyaudio.PyAudio()

        self.mic_devices = {}
        self.speaker_devices = {}
        self.recording_thread = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time_label)
        self.start_time = 0
        self.total_cycles = 0  # Contor pentru numărul de cicluri de 10 min

        self._setup_ui()
        self._load_devices()

    def _setup_ui(self):
        """Configurează elementele vizuale ale interfeței."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)

        # 1. Zona de Selecție Dispozitive
        device_group = QWidget()
        device_layout = QHBoxLayout(device_group)

        # Select Microfon
        device_layout.addWidget(QLabel("Microfon (CH1):"))
        self.mic_combo = QComboBox()
        self.mic_combo.setStyleSheet("QComboBox { min-width: 200px; }")
        device_layout.addWidget(self.mic_combo)

        # Select Boxe/Loopback
        device_layout.addWidget(QLabel("Boxe/Loopback (CH2):"))
        self.speaker_combo = QComboBox()
        self.speaker_combo.setStyleSheet("QComboBox { min-width: 200px; }")
        device_layout.addWidget(self.speaker_combo)

        main_layout.addWidget(device_group)

        # 2. Zona de Control
        control_group = QWidget()
        control_layout = QHBoxLayout(control_group)

        self.duration_input = QLineEdit(str(RECORD_SECONDS))
        self.duration_input.setFixedWidth(50)
        self.duration_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        control_layout.addWidget(QLabel("Durată Ciclu (sec):"))
        control_layout.addWidget(self.duration_input)

        self.start_button = QPushButton("START Monitorizare")
        self.start_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 10px; font-weight: bold; }")
        self.start_button.clicked.connect(self._start_recording)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("STOP Monitorizare")
        self.stop_button.setStyleSheet(
            "QPushButton { background-color: #F44336; color: white; padding: 10px; font-weight: bold; }")
        self.stop_button.clicked.connect(self._stop_recording)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        main_layout.addWidget(control_group)

        # 3. Zona de Progres și Info
        info_group = QWidget()
        info_layout = QHBoxLayout(info_group)

        self.cycle_label = QLabel("Ciclu: 0")
        self.cycle_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; margin-right: 15px; }")
        info_layout.addWidget(self.cycle_label)

        self.time_label = QLabel("Timp: 00:00")
        self.time_label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; }")
        info_layout.addWidget(self.time_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("Progres: %p%")
        info_layout.addWidget(self.progress_bar)

        main_layout.addWidget(info_group)

        # 4. Zona de Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            "QTextEdit { background-color: #2e2e2e; color: #f0f0f0; font-family: 'Consolas', 'Courier New'; font-size: 10pt; }")
        main_layout.addWidget(self.log_text)

        self._log("Interfața DJ Recorder este gata.")
        self._log(f"Directorul de salvare MP3: {RECORDINGS_DIR.resolve()}")
        self._log(f"Directorul de backup WAV: {WAV_BACKUP_DIR.resolve()}")
        self._log(setup_ffmpeg_path())  # Afișează ce cale FFmpeg folosește

    def _load_devices(self):
        """Identifică și încarcă dispozitivele PyAudio în combo box-uri."""
        self.mic_devices.clear()
        self.speaker_devices.clear()
        self.mic_combo.clear()
        self.speaker_combo.clear()

        num_devices = self.pyaudio_instance.get_device_count()

        for i in range(num_devices):
            dev_info = self.pyaudio_instance.get_device_info_by_index(i)

            # --- Îmbunătățire: Decodare Nume Dispozitiv (Remediere 'utf8') ---
            name = dev_info['name']
            if isinstance(name, bytes):
                try:
                    name = name.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        name = name.decode(sys.getdefaultencoding(), errors='replace')
                    except Exception:
                        name = "Nume Dispozitiv Necunoscut (Eroare Decodare)"
            # -------------------------------------------------------------

            # Dispozitive de INTRARE (Microfon, Stereo Mix)
            if dev_info['maxInputChannels'] > 0:
                self.mic_devices[name] = i
                self.mic_combo.addItem(f"[{i}] {name}")

            # Dispozitive care pot fi folosite pentru Loopback/Boxe (necesită *măcar* ieșire)
            if dev_info['maxOutputChannels'] > 0 or dev_info['maxInputChannels'] > 0:
                label = ""
                if dev_info['maxInputChannels'] > 0:
                    label += "(Intrare/Loopback)"
                else:
                    label += "(Doar Ieșire)"

                if name not in self.speaker_devices:
                    self.speaker_devices[name] = i
                    self.speaker_combo.addItem(f"[{i}] {name} {label}")

        self.mic_combo.setCurrentIndex(0)
        self.speaker_combo.setCurrentIndex(0)
        self._log(f"Am găsit {len(self.mic_devices)} dispozitive de Microfon.")
        self._log(f"Am găsit {len(self.speaker_devices)} dispozitive de Boxe/Loopback.")

    def _log(self, message: str):
        """Afișează un mesaj în zona de log."""
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        self.log_text.append(f"{timestamp} {message}")

    def _get_selected_ids(self):
        """Extrage ID-urile selectate din combo box-uri."""
        mic_name_part = self.mic_combo.currentText().split(']')[0].strip('[')
        speaker_name_part = self.speaker_combo.currentText().split(']')[0].strip('[')

        try:
            mic_id = int(mic_name_part)
            speaker_id = int(speaker_name_part)
            return mic_id, speaker_id
        except ValueError:
            return None, None

    def _start_recording(self):
        """Inițiază monitorizarea continuă într-un thread separat."""
        try:
            duration = int(self.duration_input.text())
        except ValueError:
            QMessageBox.warning(self, "Eroare Durată", "Durata trebuie să fie un număr întreg valid.")
            return

        mic_id, speaker_id = self._get_selected_ids()

        if mic_id is None or speaker_id is None:
            QMessageBox.critical(self, "Eroare Selecție", "Nu s-au putut identifica ID-urile dispozitivelor selectate.")
            return

        # Setează starea GUI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.mic_combo.setEnabled(False)
        self.speaker_combo.setEnabled(False)
        self.progress_bar.setValue(0)
        self.total_cycles = 0
        self.cycle_label.setText("Ciclu: 0")

        # Pornește Timer-ul pentru afișarea timpului (Resetat la fiecare ciclu)
        self.start_time = time.time()
        self.timer.start(1000)  # Actualizează la fiecare secundă

        # Pornește Thread-ul de înregistrare
        self.recording_thread = RecordingWorker(mic_id, speaker_id, duration)
        self.recording_thread.finished_cycle.connect(self._handle_cycle_completion)
        self.recording_thread.progress_update.connect(self.progress_bar.setValue)
        self.recording_thread.log_message.connect(self._log)
        self.recording_thread.start()

    def _stop_recording(self):
        """Oprește monitorizarea continuă."""
        if self.recording_thread and self.recording_thread.isRunning():
            self.recording_thread.stop()
            self.stop_button.setEnabled(False)
            self._log("STOP solicitat. Aștept finalizarea ciclului curent...")

    def _update_time_label(self):
        """Actualizează eticheta de timp"""
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60

        # Calculează timpul rămas în ciclul curent
        duration = int(self.duration_input.text())
        time_in_cycle = elapsed % duration
        remaining = duration - time_in_cycle

        self.time_label.setText(f"Timp Ciclu: {time_in_cycle:02d}s (Rămas: {remaining:02d}s)")

    def _handle_cycle_completion(self, mic_wav_path: str, speaker_wav_path: str):
        """Finalizează un singur ciclu, convertește și repornește timer-ul."""

        self.total_cycles += 1
        self.cycle_label.setText(f"Ciclu: {self.total_cycles}")

        # 1. Reset timer și progress bar pentru următorul ciclu
        self.start_time = time.time()
        self.progress_bar.setValue(0)
        self._update_time_label()

        self._log("\n--- CONVERSIE ȘI TRIMITERE DATE (Modul 3) ---")

        # 2. Conversie și gestionare WAV
        mic_mp3 = self._convert_and_cleanup(mic_wav_path, is_mic=True)
        speaker_mp3 = self._convert_and_cleanup(speaker_wav_path, is_mic=False)

        # 3. Trimiterea notificării (Simulare pentru Modulul 3)
        self._log("--- CICLU FINALIZAT ---")
        self._log(f"   ✅ CH1 MP3: {Path(mic_mp3).name if mic_mp3 else 'EȘUAT'}")
        self._log(f"   ✅ CH2 MP3: {Path(speaker_mp3).name if speaker_mp3 else 'EȘUAT/LIPSĂ'}")
        self._log("   🔔 NOTIFICARE trimisă bazei de date (Modul 3 poate începe transcrierea).")

        # Verifică dacă thread-ul a fost oprit între timp (prin apăsarea STOP)
        if not self.recording_thread.isRunning():
            self._cleanup_final()

    def _cleanup_final(self):
        """Operații de curățare finală după ce bucla s-a oprit."""
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.mic_combo.setEnabled(True)
        self.speaker_combo.setEnabled(True)
        self.progress_bar.setValue(0)
        self.time_label.setText("Timp: 00:00")
        QMessageBox.information(self, "Monitorizare Oprită",
                                f"Monitorizarea a fost oprită. S-au finalizat {self.total_cycles} cicluri complete.")

    def _convert_and_cleanup(self, wav_path: str, is_mic: bool) -> str | None:
        """Convertește WAV la MP3 folosind pydub. Păstrează WAV-ul dacă eșuează."""
        # Mutam importul pydub aici.
        try:
            from pydub import AudioSegment
        except ImportError:
            self._log("❌ EROARE CRITICĂ: Biblioteca 'pydub' nu a putut fi importată. Conversia MP3 eșuează.")
            # WAV-ul rămâne în directorul de backup cu numele original
            self._log(f"   WAV PĂSTRAT (Eroare pydub): {Path(wav_path).name}")
            return None

        if not wav_path or not os.path.exists(wav_path):
            return None

        try:
            audio = AudioSegment.from_wav(wav_path)
            # Numele MP3 va merge în directorul recordings_gui
            mp3_filename = Path(wav_path).name.replace(".wav", ".mp3")
            mp3_path = RECORDINGS_DIR / mp3_filename

            # Asigură-te că directorul final MP3 există
            os.makedirs(RECORDINGS_DIR, exist_ok=True)

            audio.export(mp3_path, format="mp3", bitrate="128k")

            # MODIFICARE CRITICĂ: Nu mai ștergem fișierul WAV după conversia reușită.
            # Acesta rămâne în directorul WAV_BACKUP_DIR.
            self._log(f"   WAV PĂSTRAT în backup: {Path(wav_path).name}")

            return str(mp3_path)

        except FileNotFoundError:
            self._log("❌ EROARE: FFmpeg nu a fost găsit. Asigură-te că este instalat.")
            self._log(f"   WAV PĂSTRAT (Eroare FFmpeg): {Path(wav_path).name}")
            return None
        except Exception as e:
            # Păstrează fișierul WAV în directorul de backup dacă conversia eșuează
            self._log(f"❌ EROARE la conversia MP3 pentru {Path(wav_path).name}: {e}.")

            # Renumește fișierul WAV pentru a indica eșecul
            failed_wav_path = Path(wav_path).with_name(f"FAILED_{Path(wav_path).name}")
            shutil.move(wav_path, failed_wav_path)
            self._log(f"   WAV mutat și redenumit: {failed_wav_path.name}")
            return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DJGUIRecorder()
    window.show()
    # Inițializează PyAudio și încarcă dispozitivele
    window.pyaudio_instance = pyaudio.PyAudio()
    window._load_devices()  # Reîncarcă dispozitivele după inițializarea PyAudio
    sys.exit(app.exec())
