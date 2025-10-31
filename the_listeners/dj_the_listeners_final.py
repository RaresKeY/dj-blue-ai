# -*- coding: utf-8 -*-
"""
DJ Listener V2 FINAL - Interfață Grafică PyQt6
Obiectiv: Înregistrare Multi-Canal WAV (Self/Others) și salvare Configurație JSON.
"""
import sys
import os
import threading
import time
import datetime
from pathlib import Path
import json  # NOU: Pentru salvarea și încărcarea configurației JSON

# --- DEPENDENȚE AUDIO ---
import pyaudio
import wave

# --- DEPENDENȚE GUI ---
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QLineEdit, QProgressBar, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

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

                    # 1. Configurare Microfon (CH1 - SELF)
                    mic_info = p.get_device_info_by_index(self.mic_id)
                    mic_stream = p.open(format=FORMAT, channels=1, rate=RATE,
                                        input=True, input_device_index=self.mic_id,
                                        frames_per_buffer=CHUNK)
                    self.log_message.emit(f"CH1 (Self/Microfon): '{mic_info['name']}' - OK.")

                    # 2. Configurare Boxe/Loopback (CH2 - OTHERS) cu Fallback
                    speaker_info = p.get_device_info_by_index(self.speaker_id)

                    try:  # Try 2 Channels
                        speaker_channels = 2
                        speaker_stream = p.open(format=FORMAT, channels=speaker_channels,
                                                rate=RATE, input=True, input_device_index=self.speaker_id,
                                                frames_per_buffer=CHUNK)
                        self.log_message.emit(f"CH2 (Others/Boxe): '{speaker_info['name']}' - 2 canale (Stereo) OK.")
                    except Exception:
                        try:  # Try 1 Channel
                            speaker_channels = 1
                            speaker_stream = p.open(format=FORMAT, channels=speaker_channels,
                                                    rate=RATE, input=True, input_device_index=self.speaker_id,
                                                    frames_per_buffer=CHUNK)
                            self.log_message.emit(
                                f"CH2 (Others/Boxe): '{speaker_info['name']}' - 1 canal (Mono Fallback) OK.")
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


# ----------------------------------------------------
# 3. CLASA PRINCIPALĂ APLICAȚIEI GUI
# ----------------------------------------------------

class DJGUIRecorder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DJ BlueAI Listener V2 (WAV Output)")
        self.setGeometry(100, 100, 750, 500)

        self.pyaudio_instance = pyaudio.PyAudio()
        self.mic_devices = {}
        self.speaker_devices = {}
        self.recording_thread = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time_label)
        self.start_time = 0
        self.total_cycles = 0

        self._setup_ui()
        self._load_devices()
        self._load_config()  # NOU: Încearcă să încarce ID-urile din JSON

    def _setup_ui(self):
        """Configurează elementele vizuale ale interfeței."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)

        # 1. Zona de Selecție Dispozitive + Salvare Config
        device_group = QWidget()
        device_layout = QHBoxLayout(device_group)

        # Select Microfon (CH1 - SELF)
        device_layout.addWidget(QLabel("SELF (Microfon):"))
        self.mic_combo = QComboBox()
        device_layout.addWidget(self.mic_combo)

        # Select Boxe/Loopback (CH2 - OTHERS)
        device_layout.addWidget(QLabel("OTHERS (Boxe/Loopback):"))
        self.speaker_combo = QComboBox()
        device_layout.addWidget(self.speaker_combo)

        # NOU: Buton pentru Salvare Configurație
        self.save_button = QPushButton("💾 SALVEAZĂ CONFIG")
        self.save_button.setStyleSheet(
            "QPushButton { background-color: #3B5B9E; color: white; padding: 5px; font-weight: bold; }")
        self.save_button.clicked.connect(self._save_config)
        device_layout.addWidget(self.save_button)

        main_layout.addWidget(device_group)

        # 2. Zona de Control (Durată, START/STOP)
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

        # 3. Zona de Progres și Info (Asemănător cu versiunea anterioară)
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

        self._log("Interfața DJ Listener V2 este gata. WAV Output.")
        self._log(f"Directorul de salvare: {RECORDINGS_DIR.resolve()}")

    def _load_devices(self):
        """Identifică și încarcă dispozitivele PyAudio în combo box-uri."""
        self.mic_devices.clear()
        self.speaker_devices.clear()
        self.mic_combo.clear()
        self.speaker_combo.clear()

        num_devices = self.pyaudio_instance.get_device_count()

        for i in range(num_devices):
            dev_info = self.pyaudio_instance.get_device_info_by_index(i)

            # Remediu pentru erorile de codare (utf8)
            name = dev_info['name']
            if isinstance(name, bytes):
                try:
                    name = name.decode('utf-8')
                except Exception:
                    name = "Nume Dispozitiv Necunoscut"

            # Dispozitive de INTRARE (Microfon - SELF)
            if dev_info['maxInputChannels'] > 0:
                self.mic_devices[name] = i
                self.mic_combo.addItem(f"[{i}] {name}")

            # Dispozitive de Ieșire/Loopback (OTHERS)
            if dev_info['maxOutputChannels'] > 0 or dev_info['maxInputChannels'] > 0:
                label = ""
                if dev_info['maxInputChannels'] > 0:
                    label = "(Intrare/Loopback)"
                else:
                    label = "(Doar Ieșire)"

                if name not in self.speaker_devices:
                    self.speaker_devices[name] = i
                    self.speaker_combo.addItem(f"[{i}] {name} {label}")

        self._log(f"Am găsit {len(self.mic_devices)} dispozitive de Microfon.")
        self._log(f"Am găsit {len(self.speaker_devices)} dispozitive de Boxe/Loopback.")

    # ------------------------------------------------------------------
    # NOU: GESTIONARE CONFIGURAȚIE JSON
    # ------------------------------------------------------------------

    def _save_config(self):
        """Salvează ID-urile dispozitivelor selectate într-un fișier JSON."""
        mic_id, speaker_id = self._get_selected_ids()
        mic_name = self.mic_combo.currentText()
        speaker_name = self.speaker_combo.currentText()

        if mic_id is None or speaker_id is None:
            QMessageBox.critical(self, "Eroare", "Selectează ambele dispozitive.")
            return

        config_data = {
            "mic_id": mic_id,
            "speaker_id": speaker_id,
            "mic_name": mic_name,
            "speaker_name": speaker_name,
            "timestamp": datetime.datetime.now().isoformat()
        }

        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            self._log(f"✅ Configurație salvată în: {CONFIG_FILE.name}")
            QMessageBox.information(self, "Succes", f"Configurația dispozitivelor a fost salvată!")

        except Exception as e:
            self._log(f"❌ EROARE la salvarea JSON: {e}")
            QMessageBox.critical(self, "Eroare Salvare", f"Nu s-a putut salva configurația: {e}")

    def _load_config(self):
        """Încarcă ID-urile salvate din JSON și le setează ca implicite."""
        if not CONFIG_FILE.exists():
            self._log("Avertisment: Fișier de configurare (JSON) lipsă.")
            return

        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)

            mic_id_saved = config_data.get("mic_id")
            speaker_id_saved = config_data.get("speaker_id")

            # Setează ID-urile în listele derulante
            self._set_combo_box_selection(self.mic_combo, mic_id_saved)
            self._set_combo_box_selection(self.speaker_combo, speaker_id_saved)

            self._log(f"✅ Configurație încărcată (Mic ID: {mic_id_saved}, Speaker ID: {speaker_id_saved})")

        except Exception as e:
            self._log(f"❌ EROARE la încărcarea JSON: {e}")

    def _set_combo_box_selection(self, combo_box: QComboBox, target_id: int):
        """Selectează un ID specific în QComboBox."""
        for i in range(combo_box.count()):
            text = combo_box.itemText(i)
            if text.startswith(f"[{target_id}]"):
                combo_box.setCurrentIndex(i)
                break

    # ------------------------------------------------------------------
    # METODE DE RULARE (Modificări minime)
    # ------------------------------------------------------------------

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
            if duration <= 0:
                raise ValueError("Durata trebuie să fie > 0.")
        except ValueError as e:
            QMessageBox.warning(self, "Eroare Durată", f"Durata trebuie să fie un număr întreg valid: {e}")
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
        self.save_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.total_cycles = 0
        self.cycle_label.setText("Ciclu: 0")

        # Pornește Timer-ul
        self.start_time = time.time()
        self.timer.start(1000)

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
        duration = int(self.duration_input.text())
        time_in_cycle = elapsed % duration
        remaining = duration - time_in_cycle

        self.time_label.setText(f"Timp Ciclu: {time_in_cycle:02d}s (Rămas: {remaining:02d}s)")

    def _handle_cycle_completion(self, self_wav_path: str, others_wav_path: str):
        """Finalizează un singur ciclu și repornește timer-ul."""

        self.total_cycles += 1
        self.cycle_label.setText(f"Ciclu: {self.total_cycles}")

        # 1. Reset timer și progress bar pentru următorul ciclu
        self.start_time = time.time()
        self.progress_bar.setValue(0)
        self._update_time_label()

        self._log("\n--- CICLU COMPLET (WAV) ---")

        # 2. Notificare (Modul 3 se așteaptă la aceste fișiere)
        self._log(f"   ✅ SELF (Microfon): {Path(self_wav_path).name}")
        self._log(f"   ✅ OTHERS (Ambient): {Path(others_wav_path).name if others_wav_path else 'LIPSĂ'}")
        self._log("   🔔 NOTIFICARE trimisă bazei de date (Modul 3 poate începe transcrierea).")

        # Verifică dacă thread-ul a fost oprit
        if not self.recording_thread.isRunning():
            self._cleanup_final()

    def _cleanup_final(self):
        """Operații de curățare finală după ce bucla s-a oprit."""
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.mic_combo.setEnabled(True)
        self.speaker_combo.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.time_label.setText("Timp: 00:00")
        QMessageBox.information(self, "Monitorizare Oprită",
                                f"Monitorizarea a fost oprită. S-au finalizat {self.total_cycles} cicluri complete.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DJGUIRecorder()
    window.show()
    sys.exit(app.exec())
