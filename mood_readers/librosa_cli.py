# -*- coding: utf-8 -*-
"""Batch audio analyser using librosa without any GUI dependencies."""
import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import numpy as np

# Usage: python3 mood_readers/librosa_test.py -o results.csv "track1.wav" "track2.mp3"

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


def _validate_file(path: Path) -> Tuple[str, str]:
    if not path.exists():
        return str(path), f"Fișierul nu există: {path}"
    if not path.is_file():
        return str(path), f"Calea nu este un fișier: {path}"
    return str(path), ""


def analyze_audio_files(file_paths: Iterable[str]) -> List[Tuple[str, dict]]:
    """Procesează o listă de fișiere audio și returnează rezultatele."""
    results: List[Tuple[str, dict]] = []
    for file_path in file_paths:
        path_obj = Path(file_path)
        validated_path, error = _validate_file(path_obj)
        if error:
            results.append((validated_path, {"error": error}))
            continue

        try:
            analysis = analyze_audio_file_logic(validated_path)
            analysis["file_name"] = Path(validated_path).name
            results.append((validated_path, analysis))
        except Exception as exc:  # noqa: BLE001 - surface full exception for CLI
            results.append((validated_path, {"error": str(exc)}))
    return results


def _format_result(result: dict) -> str:
    if "error" in result:
        return f"!!! EROARE: {result['error']}"

    return (
        f"--- Rezultat pentru: {result['file_name']} ---\n"
        f"  BPM (Energie):\t{result['bpm']} BPM\n"
        f"  Gamă (Cheie):\t\t{result['key_technical']}\n"
        f"  Camelot (Mixaj):\t{result['key_camelot']}\n"
        f"  Valență (Simplă):\t{result['valence']}\n"
        f"  MOOD DETALIAT:\t{result['mood_detailed']}\n"
        f"{'-' * 40}"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analiză batch pentru fișiere audio folosind librosa (fără GUI)."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Căi către fișiere audio ce trebuie procesate.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Scrie rezultatele într-un fișier CSV specificat.",
    )
    return parser


def _write_results_csv(destination: Path, analysis_results: List[Tuple[str, dict]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "file_path",
        "file_name",
        "bpm",
        "key_technical",
        "key_camelot",
        "valence",
        "mood_detailed",
        "error",
    ]

    with destination.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for file_path, result in analysis_results:
            row = {
                "file_path": file_path,
                "file_name": result.get("file_name", ""),
                "bpm": result.get("bpm", ""),
                "key_technical": result.get("key_technical", ""),
                "key_camelot": result.get("key_camelot", ""),
                "valence": result.get("valence", ""),
                "mood_detailed": result.get("mood_detailed", ""),
                "error": result.get("error", ""),
            }
            writer.writerow(row)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    analysis_results = analyze_audio_files(args.paths)

    successes = 0
    failures = 0

    for _, result in analysis_results:
        print(_format_result(result))
        if "error" in result:
            failures += 1
        else:
            successes += 1

    write_failed = False
    if args.output:
        output_path = Path(args.output)
        try:
            _write_results_csv(output_path, analysis_results)
            print(f"\nRezultatele au fost salvate în: {output_path}")
        except OSError as exc:
            print(f"\n!!! Nu am putut salva rezultatele: {exc}", file=sys.stderr)
            write_failed = True

    print("\n===== PROCESARE FINALIZATĂ =====")
    print(f"Fișiere procesate cu succes: {successes}")
    print(f"Fișiere eșuate: {failures}")

    if failures > 0 or write_failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
