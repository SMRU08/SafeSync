"""
scripts/audio/generate_alert_audio_videos.py
============================================
Synthesizes high-fidelity industrial audio alerts (Hindi voice announcement
with alert chime tone) for PPE violations, smoke/fire hazards, and compliance
status, and muxes the audio directly into all annotated MP4 video files.

Spoken format:
- For Missing PPE:
  "कैमरा [Camera Name]: वर्कर #[Worker ID], आपने [Missing PPE] नहीं पहना है। कृपया तुरंत सुरक्षा उपकरण पहनें!"
- For Fire / Smoke Emergency:
  "आपातकालीन चेतावनी! कैमरा [Camera Name] में आग और धुआं डिटेक्ट हुआ है। तुरंत जांच करें! इमरजेंसी, इमरजेंसी!"
- For Fully Compliant:
  "कैमरा [Camera Name]: सभी कर्मचारी पूर्ण सुरक्षा अनुपालन में हैं। साइट सुरक्षित है।"
"""

import os
import sys
import json
import math
import wave
import struct
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import imageio_ffmpeg
import edge_tts
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent.parent
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

TRANSLATIONS_HINDI = {
    "helmet": "हेलमेट",
    "safety_vest": "सेफ्टी वेस्ट",
    "gloves": "ग्लव्स",
    "safety_footwear": "सेफ्टी जूते",
}


def generate_chime_wav(output_wav: Path, sample_rate: int = 44100):
    """Generates an industrial two-tone alert chime (beep-beep)."""
    t1 = np.linspace(0, 0.15, int(sample_rate * 0.15), False)
    t_pause = np.zeros(int(sample_rate * 0.08))
    t2 = np.linspace(0, 0.25, int(sample_rate * 0.25), False)

    # 880 Hz tone then 1175 Hz tone
    beep1 = 0.6 * np.sin(2 * np.pi * 880 * t1)
    beep2 = 0.6 * np.sin(2 * np.pi * 1175 * t2)

    # Apply fade in/out to avoid clicks
    ramp1 = np.linspace(0, 1, int(len(beep1) * 0.1))
    beep1[:len(ramp1)] *= ramp1
    beep1[-len(ramp1):] *= ramp1[::-1]

    ramp2 = np.linspace(0, 1, int(len(beep2) * 0.1))
    beep2[:len(ramp2)] *= ramp2
    beep2[-len(ramp2):] *= ramp2[::-1]

    audio_signal = np.concatenate([beep1, t_pause, beep2, np.zeros(int(sample_rate * 0.2))])
    audio_int16 = (audio_signal * 32767).astype(np.int16)

    with wave.open(str(output_wav), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())


async def synthesize_speech(text: str, output_path: Path, voice: str = "hi-IN-MadhurNeural") -> bool:
    """Synthesizes Hindi neural speech using edge_tts with fallback."""
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        return True
    except Exception as e:
        print(f"    [WARN] edge-tts error: {e}. Trying fallback...")
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
            return True
        except Exception as e2:
            print(f"    [ERR] pyttsx3 fallback failed: {e2}")
            return False


def build_announcement_text(cam_label: str, summary_data: Dict[str, Any]) -> str:
    """Builds the exact Hindi announcement string based on detections."""
    incidents = summary_data.get("incidents", [])
    dets = summary_data.get("detections", {})
    haz_fire = dets.get("fire", 0)
    haz_smoke = dets.get("smoke", 0)

    # Check for fire/smoke hazard first
    if haz_fire > 0 or haz_smoke > 0:
        return (
            f"आपातकालीन चेतावनी! कैमरा {cam_label} में आग और धुआं डिटेक्ट हुआ है। "
            f"तुरंत जांच करें! इमरजेंसी! इमरजेंसी!"
        )

    # Check for PPE violations
    if incidents:
        first_inc = incidents[0]
        wid = first_inc.get("worker_id", 1)
        missing = first_inc.get("missing_equipment", [])
        if missing:
            missing_hindi = [TRANSLATIONS_HINDI.get(m, m) for m in missing]
            if len(missing_hindi) == 1:
                items_str = missing_hindi[0]
            elif len(missing_hindi) == 2:
                items_str = f"{missing_hindi[0]} और {missing_hindi[1]}"
            else:
                items_str = ", ".join(missing_hindi[:-1]) + " और " + missing_hindi[-1]
            return (
                f"सावधान! कैमरा {cam_label}: वर्कर #{wid}, आपने {items_str} नहीं पहना है। "
                f"कृपया तुरंत सुरक्षा उपकरण पहनें!"
            )

    # Compliant
    return f"कैमरा {cam_label}: सभी कर्मचारी सुरक्षा नियमों का पालन कर रहे हैं। साइट सुरक्षित है।"


def has_audio_stream(video_path: Path) -> bool:
    """Returns True if the video file has at least one audio stream."""
    try:
        result = subprocess.run(
            [FFMPEG_EXE, "-i", str(video_path), "-f", "null", "-"],
            capture_output=True, text=True
        )
        return "Audio:" in result.stderr
    except Exception:
        return False


def mux_audio_video(
    annotated_video: Path,
    alert_audio: Path,
    output_path: Path,
    video_duration: float,
    original_video: Optional[Path] = None,
) -> bool:
    """
    Mix audio into the annotated video.

    If original_video is supplied AND has an audio stream, use a 3-input amix:
      - original video audio at 70% volume (ambient / site audio)
      - alert WAV (chime + Hindi speech) at 160% volume (clearly audible over ambient)

    If original_video is absent or has no audio, fall back to simple 2-input mux
    (alert audio looped over the annotated video).
    """
    use_mix = (
        original_video is not None
        and original_video.exists()
        and has_audio_stream(original_video)
    )

    if use_mix:
        filter_complex = (
            "[1:a]volume=0.7[aorig];"
            "[2:a]volume=1.6[aalert];"
            "[aorig][aalert]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(annotated_video),
            "-i", str(original_video),
            "-stream_loop", "-1",
            "-i", str(alert_audio),
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(video_duration),
            str(output_path),
        ]
    else:
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(annotated_video),
            "-stream_loop", "-1",
            "-i", str(alert_audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(video_duration),
            "-shortest",
            str(output_path),
        ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"    [ERR] FFMPEG failed: {res.stderr[-800:]}")
        return False
    return True


async def process_directory(
    base_dir: Path,
    cameras_map: Dict[str, str],
    source_video_dirs: Optional[List[Path]] = None,
):
    videos_dir = base_dir / "annotated_videos"
    reports_dir = base_dir / "reports"
    temp_dir = base_dir / "temp_audio"
    temp_dir.mkdir(parents=True, exist_ok=True)

    if not videos_dir.exists():
        print(f"[SKIP] Directory not found: {videos_dir}")
        return

    chime_path = temp_dir / "chime.wav"
    if not chime_path.exists():
        generate_chime_wav(chime_path)

    videos = sorted(list(videos_dir.glob("*_annotated.mp4")))
    print(f"\nProcessing {len(videos)} videos in {videos_dir}:")

    for v_path in videos:
        stem = v_path.stem.replace("_annotated", "")
        summary_file = reports_dir / f"{stem}_summary.json"
        summary_data = {}
        if summary_file.exists():
            try:
                with open(summary_file, "r", encoding="utf-8") as f:
                    summary_data = json.load(f)
            except Exception:
                pass

        # Locate original source video (for audio mixing)
        orig_video: Optional[Path] = None
        if source_video_dirs:
            for src_dir in source_video_dirs:
                for ext in (".mp4", ".avi", ".mov", ".mkv", ".webm"):
                    candidate = src_dir / f"{stem}{ext}"
                    if candidate.exists():
                        orig_video = candidate
                        break
                if orig_video:
                    break

        cam_label = cameras_map.get(stem, stem)
        announcement_text = build_announcement_text(cam_label, summary_data)

        # Re-use existing combined WAV if present, otherwise regenerate
        combined_wav = temp_dir / f"{stem}_combined.wav"
        if not combined_wav.exists():
            speech_path = temp_dir / f"{stem}_speech.mp3"
            if not speech_path.exists():
                await synthesize_speech(announcement_text, speech_path)
            concat_cmd = [
                FFMPEG_EXE, "-y",
                "-i", str(chime_path),
                "-i", str(speech_path),
                "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]",
                "-map", "[out]",
                str(combined_wav),
            ]
            subprocess.run(concat_cmd, capture_output=True)

        duration = summary_data.get("duration", 10.0)
        muxed_temp = temp_dir / f"{stem}_muxed.mp4"
        orig_label = f"+ {orig_video.name}" if orig_video else "(alert-only)"
        print(f"  Mixing: {v_path.name} {orig_label}")

        success = mux_audio_video(
            annotated_video=v_path,
            alert_audio=combined_wav,
            output_path=muxed_temp,
            video_duration=duration,
            original_video=orig_video,
        )

        if success and muxed_temp.exists() and muxed_temp.stat().st_size > 1000:
            # Replace original annotated video — use shutil.move with copy+delete fallback
            try:
                import shutil
                # Remove destination first to avoid cross-device rename issues
                if v_path.exists():
                    v_path.unlink()
                shutil.move(str(muxed_temp), str(v_path))
            except Exception as move_err:
                # Last resort: copy then delete
                try:
                    import shutil as _sh
                    _sh.copy2(str(muxed_temp), str(v_path))
                    muxed_temp.unlink(missing_ok=True)
                except Exception as copy_err:
                    print(f"  [WARN] Could not replace file: {copy_err}")
            print(f"  [OK] {v_path.name} ({duration:.1f}s) | {orig_label}")
            ann = announcement_text
            print(f"       Spoken: \"{ann[:90]}...\"" if len(ann) > 90 else f"       Spoken: \"{ann}\"")
        else:
            print(f"  [FAIL] Could not mux audio for {v_path.name}")


def main():
    print("=" * 80)
    print("SafeSync — Synthesizing Audio Alerts & Muxing into All Output Videos")
    print("=" * 80)

    # Build mapping from video stem to camera name
    cameras_map = {}
    yaml_path = ROOT / "configs" / "cameras.yaml"
    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            ydata = yaml.safe_load(f) or {}
            for cam in ydata.get("cameras", []):
                src = cam.get("source", "")
                stem = Path(src).stem.replace("_annotated", "")
                cname = cam.get("name", stem)
                # Simplify to short name e.g. "CAM-01" or "CAM-19"
                short_name = cname.split("•")[0].strip() if "•" in cname else cname
                cameras_map[stem] = short_name

    # Process New folder (2) — original source videos are in the input folder itself
    dir1 = Path(r"D:\Additional\New folder (2)\output")
    asyncio.run(process_directory(
        base_dir=dir1,
        cameras_map=cameras_map,
        source_video_dirs=[
            Path(r"D:\Additional\New folder (2)"),
        ],
    ))

    # Process Safesync output2 — original source videos are in D:\Additional\Safesync
    dir2 = Path(r"D:\Additional\Safesync\output2")
    asyncio.run(process_directory(
        base_dir=dir2,
        cameras_map=cameras_map,
        source_video_dirs=[
            Path(r"D:\Additional\Safesync"),
            Path(r"D:\Additional\New folder (2)"),
        ],
    ))

    print("\n" + "=" * 80)
    print("All videos updated with original + alert audio mixed via amix!")
    print("=" * 80)


if __name__ == "__main__":
    main()
