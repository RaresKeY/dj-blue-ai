import whisper
import os
import time
from datetime import datetime
import glob  # Folosit pentru a găsi cel mai recent fișier MP3
import sys

# ----------------------------------------------------
# 1. SETĂRI ȘI CONFIGURARE
# ----------------------------------------------------

# Definirea căilor (trebuie să fie aceleași ca în Modulul 1)
MP3_DIR = "recordings_gui"  # Folder de unde preluăm fișierul MP3
TRANSCRIPT_DIR = "../The Transcribers/transcripts"  # Folder pentru salvarea rezultatelor text

# Modelul Whisper de folosit (tiny, base, small, medium, large)
# 'base' este un bun echilibru între viteză și precizie
WHISPER_MODEL = "large"

# Creează folderul de transcrieri dacă nu există
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)


# ----------------------------------------------------
# 2. FUNCȚII DE PROCESARE
# ----------------------------------------------------

def find_latest_mp3(directory):
    """
    Găsește calea absolută către cel mai recent fișier .mp3 din director.
    """
    # Folosește glob pentru a găsi toate fișierele MP3
    list_of_files = glob.glob(os.path.join(directory, '*.mp3'))

    if not list_of_files:
        print(f"❌ Eroare: Nu a fost găsit niciun fișier MP3 în directorul '{directory}'.")
        return None

    # Găsește cel mai recent fișier pe baza timpului de creare (cel mai recent înregistrat)
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


def transcribe_audio(audio_path):
    """
    Încarcă modelul Whisper și transcrie fișierul audio specificat.
    """
    if not audio_path:
        return "Nicio transcriere: Fișierul audio nu a fost găsit."

    print(f"--- Încărc modelul Whisper '{WHISPER_MODEL}'...")
    try:
        # Încărcarea modelului în memorie. Poate dura puțin prima dată.
        # Descarcă modelul de pe internet prima dată când rulează.
        model = whisper.load_model(WHISPER_MODEL)
        print("✅ Model încărcat.")
    except Exception as e:
        print(f"❌ Eroare la încărcarea modelului Whisper: {e}")
        print("   Asigură-te că ai instalat 'openai-whisper' și dependențele necesare.")
        return "Eroare de model."

    print(f"--- Încep transcrierea fișierului: {os.path.basename(audio_path)}...")
    start_time = time.time()

    # Procesul de transcriere
    # fp16=False este adăugat pentru compatibilitate pe sisteme fără GPU
    # language="ro" specifică limba română pentru precizie maximă
    result = model.transcribe(audio_path, fp16=False, language="ro")

    end_time = time.time()
    duration = end_time - start_time

    print(f"✅ Transcriere finalizată în {duration:.2f} secunde.")

    # Whisper returnează un dicționar cu rezultatul (cheia 'text' este cea importantă)
    return result["text"]


def save_transcript(text_content):
    """
    Salvează textul transcris într-un fișier .txt în folderul 'transcripts'.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_filename = f"transcript_{timestamp}.txt"
    transcript_path = os.path.join(TRANSCRIPT_DIR, transcript_filename)

    try:
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(text_content)

        print(f"✅ Transcriere salvată cu succes: {transcript_path}")
    except Exception as e:
        print(f"❌ Eroare la salvarea fișierului text: {e}")


# ----------------------------------------------------
# 3. BUCLA PRINCIPALĂ DE TRANSCRIERE
# ----------------------------------------------------

def main():
    print("--- DJ BLUEAI TRANSLATOR STARTAT ---")

    # 1. Găsește cel mai recent fișier MP3 creat de Modulul 1
    audio_file_to_transcribe = find_latest_mp3(MP3_DIR)

    if not audio_file_to_transcribe:
        print("Oprire: Nu s-a găsit niciun fișier MP3 de procesat.")
        return

    # 2. Transcrie fișierul
    transcript_text = transcribe_audio(audio_file_to_transcribe)

    # 3. Afișează și salvează rezultatul
    if transcript_text:
        print("\n--- REZULTAT TRANSCRIERE ---")
        print(transcript_text)
        print("----------------------------")

        save_transcript(transcript_text)


if __name__ == "__main__":
    main()
