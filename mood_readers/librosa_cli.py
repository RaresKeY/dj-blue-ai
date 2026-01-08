# -*- coding: utf-8 -*-
"""Batch audio analyser using librosa without any GUI dependencies."""
import argparse
import csv
import sys
import io
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import numpy as np

# Usage: python3 mood_readers/librosa_cli.py -o results.csv "track1.wav" "track2.mp3"

# --- LIBROSA DEPENDENCIES ---
# Ensure everything is installed from requirements.txt
try:
    import librosa
    import librosa.beat
    import soundfile as sf
except ImportError:
    print("ERROR: librosa is missing. Run: pip install -r requirements.txt")
    sys.exit(1)

# ----------------------------------------------------
# 1. LIBROSA ANALYSIS LOGIC
# ----------------------------------------------------

# Camelot translation table
CAMELOT_WHEEL = {
    'C': ('8B', '5A'), 'G': ('9B', '6A'), 'D': ('10B', '7A'), 'A': ('11B', '8A'),
    'E': ('12B', '9A'), 'B': ('1B', '10A'), 'F#': ('2B', '11A'), 'Db': ('3B', '12A'),
    'Ab': ('4B', '1B'), 'Eb': ('5B', '2A'), 'Bb': ('6B', '3A'), 'F': ('7B', '4A'),
    'C#': ('3B', '12A'), 'D#': ('5B', '2A'), 'G#': ('4B', '1B'), 'A#': ('6B', '3A'),
    'Am': ('8B', '5A'), 'Em': ('9B', '6A'), 'Bm': ('10B', '7A'), 'F#m': ('11B', '8A'),
    'C#m': ('12B', '9A'), 'G#m': ('1B', '10A'), 'D#m': ('2B', '11A'), 'A#m': ('3B', '12A'),
    'Fm': ('4B', '1B'), 'Cm': ('5B', '2A'), 'Gm': ('6B', '3A'), 'Dm': ('7B', '4A')
}

# Standard notes mapping
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def get_camelot_code(key: str) -> str:
    """Translates a technical key (e.g. 'C#min') into Camelot code (e.g. '12A')"""
    if key.endswith('maj'):
        base_key = key[:-3]
        return CAMELOT_WHEEL.get(base_key, ('N/A', 'N/A'))[0]
    elif key.endswith('min'):
        base_key = key[:-3]
        return CAMELOT_WHEEL.get(base_key, ('N/A', 'N/A'))[1]
    return "N/A"


def get_detailed_mood(bpm: int, is_major: bool) -> str:
    """
    NEW: Combines BPM (Arousal) and Scale (Valence) to return a detailed mood.
    This is the Circumplex Model (Mood Matrix).
    """
    if is_major:
        # --- POSITIVE AXIS (Major Scale) ---
        if bpm > 130:
            return "Euphoric / Party (High Arousal)"
        elif bpm > 95:
            return "Happy / Optimistic (Medium Arousal)"
        else:
            return "Calm / Quiet (Low Arousal)"
    else:
        # --- NEGATIVE AXIS (Minor Scale) ---
        if bpm > 125:
            return "Tense / Aggressive (High Arousal)"
        elif bpm > 90:
            return "Melancholic / Nostalgic (Medium Arousal)"
        else:
            return "Sad / Dark (Low Arousal)"


def _analyze_signal(y: np.ndarray, sr: int) -> dict:
    """Internal logic to extract features from loaded audio signal."""
    # 1. BPM DETECTION
    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        # Handle different librosa versions where tempo might be scalar or array
        if np.ndim(tempo) > 0:
             bpm = int(tempo[0])
        else:
             bpm = int(tempo)
    except Exception:
        bpm = 0

    # 2. KEY DETECTION
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)
    chroma_vector = np.mean(chroma, axis=1)

    C_major_template = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    A_minor_template = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 4.20])

    best_key = "Unknown"
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
    valence_simple = "Positive (Major)" if is_major else "Negative (Minor)"

    # --- MODIFICATION: Call the new detailed mood function ---
    mood_detailed = get_detailed_mood(bpm, is_major)

    return {
        "bpm": bpm,
        "key_technical": best_key,
        "key_camelot": camelot_code,
        "valence": valence_simple,
        "mood_detailed": mood_detailed
    }


def analyze_audio_bytes_logic(audio_bytes: bytes) -> dict:
    """
    Analyzes audio bytes directly (WAV/MP3/etc formats expected).
    Useful for in-memory processing without temp files.
    """
    target_sr = 22050
    try:
        # Wrap bytes in BytesIO so librosa/soundfile can read it
        audio_file = io.BytesIO(audio_bytes)
        y, sr = librosa.load(audio_file, sr=target_sr, mono=True)
        return _analyze_signal(y, sr)
    except Exception as e:
        return {
            "bpm": 0,
            "key_technical": "Error",
            "key_camelot": "N/A",
            "valence": "Error",
            "mood_detailed": f"Error: {str(e)}"
        }


def analyze_audio_file_logic(file_path: str) -> dict:
    """Function that runs Librosa calculations and returns a dictionary of results."""

    # OPTIMIZATION: Analyze a representative chunk (e.g., 45s from middle)
    # and use a lower sample rate (22050 Hz is standard for feature extraction).
    target_sr = 22050
    analyze_duration = 45.0
    
    try:
        # Quickly get duration to find the middle
        # Note: librosa.get_duration(path=...) works in newer librosa versions.
        # If it fails, we fall back to loading from start.
        total_duration = librosa.get_duration(path=file_path)
        offset = max(0, (total_duration - analyze_duration) / 2)
    except Exception:
        # Fallback: Just load the first 45 seconds if duration check fails
        offset = 0.0

    # Load only the specific segment
    y, sr = librosa.load(file_path, sr=target_sr, mono=True, offset=offset, duration=analyze_duration)

    return _analyze_signal(y, sr)


def _validate_file(path: Path) -> Tuple[str, str]:
    if not path.exists():
        return str(path), f"File does not exist: {path}"
    if not path.is_file():
        return str(path), f"Path is not a file: {path}"
    return str(path), ""


def analyze_audio_files(file_paths: Iterable[str]) -> List[Tuple[str, dict]]:
    """Processes a list of audio files and returns the results."""
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
        return f"!!! ERROR: {result['error']}"

    return (
        f"--- Result for: {result['file_name']} ---\n"
        f"  BPM (Energy):\t{result['bpm']} BPM\n"
        f"  Key (Technical):\t\t{result['key_technical']}\n"
        f"  Camelot (Mix):\t{result['key_camelot']}\n"
        f"  Valence (Simple):\t{result['valence']}\n"
        f"  DETAILED MOOD:\t{result['mood_detailed']}\n"
        f"{'-' * 40}"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch analysis for audio files using librosa (without GUI)."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Paths to audio files to be processed.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write results to a specified CSV file.",
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
            save_analysis_to_json(output_path, analysis_results[0][1], output_path.with_suffix('.json'))
            print(f"\nResults have been saved to: {output_path}")
        except OSError as exc:
            print(f"\n!!! Could not save results: {exc}", file=sys.stderr)
            write_failed = True

    print("\n===== PROCESSING COMPLETE =====")
    print(f"Files successfully processed: {successes}")
    print(f"Failed files: {failures}")

    if failures > 0 or write_failed:
        return 1
    return 0

#function that saves camelot and bpm to a json file
def save_analysis_to_json(file_path: str, analysis: dict, json_path: str) -> None:
    """Saves the analysis to a JSON file."""
    import json

    data_to_save = {
        "file_name": analysis.get("file_name", ""),
        "bpm": analysis.get("bpm", ""),
        "key_camelot": analysis.get("key_camelot", ""),
        "mood_detailed": analysis.get("mood_detailed", "")
    }

    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(data_to_save, json_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    sys.exit(main())








