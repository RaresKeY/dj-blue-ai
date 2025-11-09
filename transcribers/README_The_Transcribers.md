# The Transcribers – Audio to Text GUI

Aplicatia transforma fisiere audio (`.mp3`, `.wav`, `.m4a`) in **transcrieri text** (JSON) si, optional, **subtitrari** (`.srt`). Este livrabilul echipei **The Transcribers** din proiectul “Music/DJ Assistant”.

---

## Ce face (pe scurt)
- Proceseaza **batch** fisiere audio selectate manual sau dintr-un folder.
- Conversie audio → **Whisper** (offline) sau **Google Web Speech** (optional, online).
- Salveaza **JSON** (schema standard) si optional **SRT**.
- Pastreaza **doar ultimele 3** transcrieri (setare „Keep last”).  
- Log in timp real + progress bar. Erorile pe un fisier **nu opresc** procesarea celorlalte.

---

## Cerinte de sistem
- **OS**: Windows 10/11, macOS 12+, Ubuntu/Debian (recomandat).
- **Python**: 3.10 – 3.12 (Tkinter este inclus in standard library).
- **FFmpeg**: necesar pentru conversia audio (mono 16 kHz).

### Instalare FFmpeg
- **Ubuntu/Debian**:
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```
- **macOS** (Homebrew):
  ```bash
  brew install ffmpeg
  ```
- **Windows**: descarca „ffmpeg-gpl” de pe https://www.gyan.dev/ffmpeg/builds/ , dezarhiveaza si adauga folderul `bin` in `PATH` (sau foloseste managerul [Chocolatey] `choco install ffmpeg`).

---

## Instalare dependinte Python
Se recomanda un **virtual environment** separat.

```bash
# 1) (optional) creaza si activeaza venv
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 2) actualizeaza pip
pip install --upgrade pip

# 3) pachete necesare
pip install faster-whisper SpeechRecognition pydub
```
> `SpeechRecognition` si `pydub` sunt **necesare doar** pentru motorul „Google”. Pentru Whisper sunt suficiente `faster-whisper` + `ffmpeg`.

---

## Fisierele din proiect
- `transcribers_gui.py` – aplicatia GUI.
- `Received/transcripts/` – **folderul implicit** de output (poate fi schimbat din UI).
- (optional) `data/` – poti folosi alt folder de output, de exemplu `data/transcripts/`.

---

## Cum rulezi
Din folderul proiectului:
```bash
# activeaza venv (daca exista), apoi:
python transcribers_gui.py
```
### In aplicatie
1. **Adauga fisiere** sau **Adauga folder** (accepta `.mp3`, `.wav`, `.m4a`).  
2. Alege **Engine**:
   - **whisper** – recomandat (offline, nelimitat).  
   - **google** – demo online, limitat (~50 request/zi), doar pentru teste.
3. Alege **Model** (Whisper):  
   - `tiny`/`base` – foarte rapid pentru test.  
   - `small` – echilibru calitate/CPU (recomandat).  
   - `medium`/`large-v2`/`large-v3` – calitate mai buna, dar mai lent/cer GPU.
4. Optiuni:
   - **Denoise Audio** – mici filtre de curatare si normalizare (FFmpeg).  
   - **Export SRT Subtitles** – salveaza si `.srt` pe langa `.json`.  
   - **Keep last** – cate transcrieri sa ramana in total (default 3).  
   - **Output** – alege folderul unde se salveaza rezultatele.
5. Apasa **START**. Poti opri cu **STOP** (se opreste dupa fisierul curent).

---

## Unde se salveaza rezultatele
- In folderul „Output” setat in UI (implicit: `Received/transcripts/`).  
- Daca ai adaugat un **folder**, se pastreaza structura relativa a subfolderelor.  
- Pentru fiecare fisier audio se scriu:
  - `NumeFisier.json` – transcriere + metadate,
  - `NumeFisier.srt` – (optional) subtitrari.

---

## Formatul JSON (schema)
```json
{
  "version": "1.0",
  "timestamp": "2025-10-20T12:34:56Z",
  "source_file": "exemplu.mp3",
  "duration_sec": 123.4,
  "language": "ro",
  "language_confidence": 0.99,
  "text": "textul concatenat al tuturor segmentelor",
  "segments": [
    { "start": 0.0, "end": 3.2, "text": "Primul segment" },
    { "start": 3.2, "end": 7.9, "text": "Al doilea segment" }
  ],
  "metadata": {
    "engine": "faster-whisper",
    "model": "small",
    "denoise": true,
    "processed_at": "2025-10-20T12:34:56.789123"
  }
}
```
> In fisierul `.srt`, timpii sunt aceiasi ca in `segments`.

---

## Sfaturi de utilizare
- Pentru verificari rapide, seteaza `Model = tiny`. Pentru calitate, `small` este un bun compromis pe CPU.
- Daca fisierul e foarte lung, ia in calcul ca procesarea pe CPU poate dura. Incearca initial pe un clip de 20–60s.
- Daca vezi in log „Saved: ….json” dar nu gasesti fisierul, verifica **calea „Output”** din UI (e afisata si la final in sumar).

---

## Troubleshooting
- **`ffmpeg: command not found`** → Instaleaza FFmpeg (vezi sectiunea dedicata) si reporneste terminalul.
- **`faster_whisper` missing** → `pip install faster-whisper` in acelasi venv in care rulezi aplicatia.
- **Google engine da eroare / rate-limit** → E normal pe FREE tier. Foloseste **Whisper** pentru productivitate.
- **„No speech detected”** → Portiuni foarte tacute; verifica ca sursa are audio util sau debifeaza „Denoise”.
- **Output gresit** → Seteaza corect folderul in campul **Output** din UI sau apasa „Browse…”.

---

## Conform cerintelor proiectului (checklist)
- [x] Converteste toate `.mp3` primite in **text** (si `.wav/.m4a` suportate).  
- [x] Foloseste **Whisper** (offline) sau **Google Speech API** (optional).  
- [x] Salveaza **JSON** in acelasi **struct** relativ al folderelor.  
- [x] Manevreaza erorile; nu blocheaza batch-ul.  
- [x] Pastreaza **ultimele 3** transcrieri (configurabil).

---

## Licente si date
- Whisper (OpenAI) via `faster-whisper` (licentiere permissive).
- Google Web Speech API – serviciu online cu limitari; folosire pe raspunderea ta.
- Asigura-te ca ai **dreptul legal** sa procesezi audio-urile pe care le incarci.

---

## Intrebari / help
Deschide „Processing Log” din UI si copiaza mesajele de eroare. De obicei sunt de ajuns pentru a diagnostica rapid problemele. Pentru suport, ofera:
- OS + versiune Python,
- log complet,
- comanda de rulare (daca e cazul),
- tipul de engine si modelul ales.
