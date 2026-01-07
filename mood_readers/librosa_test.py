# -*- coding: utf-8 -*-
"""
Analizor Muzical GUI (PyQt6) - VERSIUNE BATCH (Lot)
Interfață pentru a selecta MULTIPLE fișiere audio și a le extrage BPM, Gamă și Codul Camelot.
"""
import sys
import os
import threading
from pathlib import Path
import numpy as np

# --- DEPENDENȚE GUI ---
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QMessageBox, QFileDialog, QTextEdit,
    QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- DEPENDENȚE LIBROSA ---
# Ne asiguram ca s-a instalat totul din requirements.txt
try:
    import librosa
    import librosa.beat
    import soundfile as sf
except ImportError:
    print("EROARE: Lipsește librosa. Rulează: pip install -r requirements.txt")
    sys.exit(1)

# ----------------------------------------------------
# 1. LOGICA DE ANALIZĂ LIBROSA
# ----------------------------------------------------

# Tabelul de traducere Camelot
CAMELOT_WHEEL = {
    'C': ('8B', '5A'), 'G': ('9B', '6A'), 'D': ('10B', '7A'), 'A': ('11B', '8A'),
    'E': ('12B', '9A'), 'B': ('1B', '10A'), 'F#': ('2B', '11A'), 'Db': ('3B', '12A'),
    'Ab': ('4B', '1B'), 'Eb': ('5B', '2A'), 'Bb': ('6B', '3A'), 'F': ('7B', '4A'),
    'C#': ('3B', '12A'), 'D#': ('5B', '2A'), 'G#': ('4B', '1B'), 'A#': ('6B', '3A'),
    'Am': ('8B', '5A'), 'Em': ('9B', '6A'), 'Bm': ('10B', '7A'), 'F#m': ('11B', '8A'),
    'C#m': ('12B', '9A'), 'G#m': ('1B', '10A'), 'D#m': ('2B', '11A'), 'A#m': ('3B', '12A'),
    'Fm': ('4B', '1B'), 'Cm': ('5B', '2A'), 'Gm': ('6B', '3A'), 'Dm': ('7B', '4A')
}

# Maparea notelor standard
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def get_camelot_code(key: str) -> str:
    """Traduce o cheie tehnică (ex: 'C#min') în cod Camelot (ex: '12A')"""
    if key.endswith('maj'):
        base_key = key[:-3]
        return CAMELOT_WHEEL.get(base_key, ('N/A', 'N/A'))[0]
    elif key.endswith('min'):
        base_key = key[:-3]
        return CAMELOT_WHEEL.get(base_key, ('N/A', 'N/A'))[1]
    return "N/A"


def get_detailed_mood(bpm: int, is_major: bool) -> str:
    """
    NOU: Combină BPM (Arousal) și Gama (Valență) pentru a returna un mood detaliat.
    Acesta este Modelul Circumplex (Matricea de Stări).
    """
    if is_major:
        # --- AXA POZITIVĂ (Gamă Majoră) ---
        if bpm > 130:
            return "Euforic / Petrecere (Arousal Ridicat)"
        elif bpm > 95:
            return "Vesel / Optimist (Arousal Mediu)"
        else:
            return "Calm / Liniștit (Arousal Scăzut)"
    else:
        # --- AXA NEGATIVĂ (Gamă Minoră) ---
        if bpm > 125:
            return "Tensionat / Agresiv (Arousal Ridicat)"
        elif bpm > 90:
            return "Melancolic / Nostalgic (Arousal Mediu)"
        else:
            return "Trist / Întunecat (Arousal Scăzut)"


def analyze_audio_file_logic(file_path: str) -> dict:
    """Funcția care rulează calculele Librosa și returnează un dicționar de rezultate."""

    y, sr = librosa.load(file_path, sr=None, mono=True)

    # 1. DETECTAREA BPM
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    bpm = int(tempo[0])  # Corecția __round__

    # 2. DETECTAREA GAMEI (Cheia Muzicală)
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)
    chroma_vector = np.mean(chroma, axis=1)

    C_major_template = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    A_minor_template = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 4.20])

    best_key = "Necunoscut"
    best_correlation = -1
    is_major = False

    for i in range(12):
        corr_maj = np.corrcoef(chroma_vector, np.roll(C_major_template, i))[0, 1]
        corr_min = np.corrcoef(chroma_vector, np.roll(A_minor_template, i))[0, 1]

        if corr_maj > best_correlation or corr_min > best_correlation:
            is_major = corr_maj > corr_min
            best_correlation = max(corr_maj, corr_min)
            best_key = NOTES[i]
            best_key += "maj" if is_major else "min"

    camelot_code = get_camelot_code(best_key)
    valence_simple = "Pozitivă (Major)" if is_major else "Negativă (Minor)"

    # --- MODIFICARE: Apelăm noua funcție de detaliere a emoției ---
    mood_detailed = get_detailed_mood(bpm, is_major)

    return {
        "bpm": bpm,
        "key_technical": best_key,
        "key_camelot": camelot_code,
        "valence": valence_simple,  # Păstrăm și valența simplă
        "mood_detailed": mood_detailed  # Adăugăm noul mood detaliat
    }


# ----------------------------------------------------
# 2. CLASA WORKER PENTRU ANALIZĂ ÎN FUNDAL
# ----------------------------------------------------

class BatchAnalysisWorker(QThread):

    file_processed = pyqtSignal(dict)  # Emite după fiecare fișier
    batch_complete = pyqtSignal(int, int)  # Emite la final (succes, eșecuri)
    analysis_error = pyqtSignal(str)

    def __init__(self, file_paths: list):  #Primește o listă de fișiere
        super().__init__()
        self.file_paths = file_paths
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        successful_files = 0
        failed_files = 0

        for file_path in self.file_paths:
            if not self._is_running:
                break

            try:
                # Rulează funcția de analiză Librosa
                results = analyze_audio_file_logic(file_path)
                results['file_name'] = Path(file_path).name  # Adaugă numele fișierului la rezultate
                self.file_processed.emit(results)
                successful_files += 1
            except Exception as e:
                # Emite eroarea, dar continuă cu următorul fișier
                error_msg = f"Eroare la procesarea {Path(file_path).name}: {e}"
                self.analysis_error.emit(error_msg)
                failed_files += 1

        if self._is_running:
            # Emite semnalul de finalizare doar dacă nu a fost oprit manual
            self.batch_complete.emit(successful_files, failed_files)


# ----------------------------------------------------
# 3. CLASA PRINCIPALĂ A APLICAȚIEI GUI
# ----------------------------------------------------

class LibrosaBatchGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Librosa Audio Analyzer (BATCH MODE)")
        self.setGeometry(100, 100, 800, 600)

        self.file_paths = []  # Stochează lista de fișiere de procesat
        self.worker_thread = None

        self._setup_ui()

    def _setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 1. Zona de Control (Butoane)
        control_layout = QHBoxLayout()

        self.browse_button = QPushButton("Adaugă Fișiere (Selectare Multiplă)...")
        self.browse_button.clicked.connect(self._browse_files)  # Nume nou: _browse_files
        control_layout.addWidget(self.browse_button)

        self.clear_button = QPushButton("Curăță Lista")
        self.clear_button.clicked.connect(self._clear_list)
        control_layout.addWidget(self.clear_button)

        self.analyze_button = QPushButton("ANALIZEAZĂ LOTUL")
        self.analyze_button.setStyleSheet(
            "QPushButton { background-color: #2E8B57; color: white; padding: 10px; font-weight: bold; }")
        self.analyze_button.clicked.connect(self._start_analysis)
        self.analyze_button.setEnabled(False)
        control_layout.addWidget(self.analyze_button)

        self.stop_button = QPushButton("OPREȘTE")
        self.stop_button.setStyleSheet(
            "QPushButton { background-color: #B22222; color: white; padding: 10px; font-weight: bold; }")
        self.stop_button.clicked.connect(self._stop_analysis)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        self.save_button = QPushButton("Salvează Rezultatele…")
        self.save_button.clicked.connect(self._save_results_to_file)
        self.save_button.setEnabled(False)
        control_layout.addWidget(self.save_button)

        main_layout.addLayout(control_layout)

        # 2. Zona de Liste (Fișiere și Rezultate)
        lists_layout = QHBoxLayout()

        # MODIFICARE: QListWidget pentru fișiere
        files_vbox = QVBoxLayout()
        files_vbox.addWidget(QLabel("Fișiere de procesat:", styleSheet="font-weight: bold;"))
        self.file_list_widget = QListWidget()
        self.file_list_widget.setStyleSheet("background-color: #f0f0f0;")
        files_vbox.addWidget(self.file_list_widget)
        lists_layout.addLayout(files_vbox)

        # MODIFICARE: QTextEdit pentru rezultate (Log)
        results_vbox = QVBoxLayout()
        results_vbox.addWidget(QLabel("Rezultate (Jurnal):", styleSheet="font-weight: bold;"))
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("background-color: #2e2e2e; color: #f0f0f0; font-family: 'Consolas';")
        results_vbox.addWidget(self.results_text)
        lists_layout.addLayout(results_vbox)

        main_layout.addLayout(lists_layout)

        # 3. Zona de Status
        self.status_label = QLabel("Gata. Adaugă fișiere pentru a începe.")
        self.status_label.setStyleSheet("color: gray; margin-top: 5px;")
        main_layout.addWidget(self.status_label)

    def _browse_files(self):
        """Deschide dialogul de selecție MULTIPLĂ fișiere."""

        #QFileDialog.getOpenFileNames (plural)
        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            "Selectează Fișiere Audio (Selectare Multiplă)",
            "",
            "Audio Files (*.mp3 *.wav);;All Files (*)"
        )

        if file_names:
            added_count = 0
            for f_path in file_names:
                if f_path not in self.file_paths:
                    self.file_paths.append(f_path)
                    self.file_list_widget.addItem(Path(f_path).name)
                    added_count += 1

            self.analyze_button.setEnabled(True)
            self.status_label.setText(f"Adăugate {added_count} fișiere. Gata de analiză.")
            self.results_text.clear()

    def _clear_list(self):
        """Curăță lista de fișiere și rezultatele."""
        self.file_paths.clear()
        self.file_list_widget.clear()
        self.results_text.clear()
        self.analyze_button.setEnabled(False)
        self.status_label.setText("Listă curățată. Adaugă fișiere noi.")
        self._update_save_button_state()

    def _start_analysis(self):
        """Porneste analiza în lot (batch) intr-un thread separat."""
        if not self.file_paths:
            QMessageBox.warning(self, "Eroare", "Nu sunt fișiere în listă.")
            return

        self.status_label.setText(f"Analiză în curs pentru {len(self.file_paths)} fișiere...")
        self.analyze_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.results_text.clear()
        self._update_save_button_state()

        # Porneste Worker-ul de Analiză (cu lista de fișiere)
        self.worker_thread = BatchAnalysisWorker(self.file_paths)
        self.worker_thread.file_processed.connect(self._handle_file_result)
        self.worker_thread.batch_complete.connect(self._handle_batch_complete)
        self.worker_thread.analysis_error.connect(self._display_error)
        self.worker_thread.start()

    def _stop_analysis(self):
        """Oprește forțat worker-ul de analiză."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.status_label.setText("Oprire solicitată... Se finalizează fișierul curent.")
            self.stop_button.setEnabled(False)

    def _handle_file_result(self, results: dict):
        """Afișează rezultatul pentru UN FIȘIER în jurnal (log)."""
        output = (
            f"--- Rezultat pentru: {results['file_name']} ---\n"
            f"  BPM (Energie):\t{results['bpm']} BPM\n"
            f"  Gamă (Cheie):\t\t{results['key_technical']}\n"
            f"  Camelot (Mixaj):\t{results['key_camelot']}\n"
            f"  Valență (Simplă):\t{results['valence']}\n"
            f"  MOOD DETALIAT:\t{results['mood_detailed']}\n"
            f"{'-' * 40}\n"
        )
        self.results_text.append(output)  # Folosim append() pentru a adăuga la log
        self._update_save_button_state()

    def _handle_batch_complete(self, successful: int, failed: int):
        """Se apelează când tot lotul este gata."""
        self.status_label.setText(f"Procesare în lot finalizată. Succes: {successful}, Eșecuri: {failed}")
        self.results_text.append(f"\n===== PROCESARE FINALIZATĂ =====")
        self.results_text.append(f"Fișiere procesate cu succes: {successful}")
        self.results_text.append(f"Fișiere eșuate: {failed}")

        self._reset_buttons()
        self._update_save_button_state()

    def _display_error(self, message: str):
        """Afișează o eroare în jurnal (log)."""
        self.results_text.append(f"!!! EROARE: {message}\n{'-' * 40}\n")
        self._update_save_button_state()

    def _reset_buttons(self):
        """Resetează butoanele la starea inițială."""
        self.analyze_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._update_save_button_state()

    def _update_save_button_state(self):
        """Activează butonul de salvare doar când există conținut în jurnal."""
        has_content = bool(self.results_text.toPlainText().strip())
        self.save_button.setEnabled(has_content)

    def _save_results_to_file(self):
        """Permite utilizatorului să salveze jurnalul curent într-un fișier text."""
        content = self.results_text.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "Nimic de salvat", "Nu există rezultate de exportat încă.")
            return

        default_name = str(Path.home() / "rezultate_librosa.txt")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează rezultatele analizelor",
            default_name,
            "Text Files (*.txt);;All Files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as file_handler:
                file_handler.write(content + "\n")
            QMessageBox.information(self, "Succes", f"Rezultatele au fost salvate în:\n{file_path}")
        except OSError as exc:
            QMessageBox.critical(self, "Eroare la salvare", f"Nu s-a putut salva fișierul:\n{exc}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LibrosaBatchGUI()
    window.show()
    sys.exit(app.exec())


