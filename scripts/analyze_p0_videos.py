"""
scripts/analyze_p0_videos.py — SafeSync P0 Video Analysis CLI
Batch processes all recorded CCTV videos in D:\\P0 using existing SafeSync pipeline.
Outputs annotated videos and summary JSON files to D:\\P0\\output.
"""

import os
import sys
import time
import argparse
import logging

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_ROOT = os.path.join(ROOT, "backend")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.services.p0_video_analyzer import P0VideoAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("p0_cli")


def print_progress(current: int, total: int, fps: float, video_name: str):
    percent = (current / total) * 100 if total > 0 else 0
    bar_len = 25
    filled = int(bar_len * current // max(1, total))
    bar = "=" * filled + "-" * (bar_len - filled)
    sys.stdout.write(
        f"\r[{bar}] {percent:5.1f}% | Frame {current}/{total} | Video: {video_name[:24]:24s} "
    )
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="SafeSync — P0 Recorded CCTV Video Analysis")
    parser.add_argument("--input-dir", "-i", type=str, default=r"D:\P0", help="Directory containing input videos")
    parser.add_argument("--output-dir", "-o", type=str, default=r"D:\P0\output", help="Directory for annotated videos")
    parser.add_argument("--batch-size", "-b", type=int, default=16, help="Batch size for vectorized inference")
    parser.add_argument("--video", "-v", type=str, default=None, help="Process single specific video only (optional)")
    parser.add_argument("--skip-existing", "-s", action="store_true", help="Skip videos that already have verified annotated MP4 and summary JSON")
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 70)
    print("  SAFESYNC — P0 RECORDED CCTV VIDEO ANALYSIS PIPELINE")
    print("=" * 70)
    print(f"  Input Directory   : {input_dir}")
    print(f"  Output Directory  : {output_dir}")
    print(f"  Inference Batch   : {args.batch_size}")
    print("=" * 70 + "\n")

    analyzer = P0VideoAnalyzer(batch_size=args.batch_size)

    if args.video:
        target_video = os.path.abspath(args.video)
        if not os.path.isfile(target_video):
            target_video = os.path.join(input_dir, args.video)
        video_files = [target_video] if os.path.isfile(target_video) else []
    else:
        video_files = analyzer.scan_videos(input_dir)

    print(f"Found {len(video_files)} video(s) for analysis:\n")
    for idx, v in enumerate(video_files, 1):
        size_mb = os.path.getsize(v) / (1024 * 1024)
        print(f"  {idx:2d}. {os.path.basename(v)} ({size_mb:.1f} MB)")
    print("\n" + "-" * 70 + "\n")

    if not video_files:
        print("[!] No supported videos found. Exiting.")
        sys.exit(0)

    overall_start = time.perf_counter()
    results = []
    successful_count = 0
    failed_count = 0

    for idx, vpath in enumerate(video_files, 1):
        vname = os.path.basename(vpath)

        if args.skip_existing:
            bname = os.path.splitext(vname)[0]
            out_mp4 = os.path.join(output_dir, f"{bname}_annotated.mp4")
            out_sum = os.path.join(output_dir, f"{bname}_summary.json")
            if os.path.isfile(out_mp4) and os.path.isfile(out_sum) and os.path.getsize(out_mp4) > 1000:
                try:
                    import json
                    with open(out_sum, "r", encoding="utf-8") as sf:
                        existing_sum = json.load(sf)
                    if existing_sum.get("status") == "COMPLETED":
                        print(f"[{idx}/{len(video_files)}] Skipping (already completed): {vname}")
                        results.append(existing_sum)
                        successful_count += 1
                        print("-" * 70)
                        continue
                except Exception:
                    pass

        print(f"[{idx}/{len(video_files)}] Processing: {vname} ...")

        try:
            summary = analyzer.process_video(
                video_path=vpath,
                output_dir=output_dir,
                progress_callback=print_progress,
            )
            print() # Newline after progress bar
            results.append(summary)

            if summary.get("status") == "COMPLETED":
                successful_count += 1
                print(
                    f"  ✓ COMPLETED: {summary['frames_processed']} frames in {summary['processing_time']}s "
                    f"({summary['effective_processing_fps']} FPS) | Violations: {summary['confirmed_ppe_violations']} | "
                    f"Fire: {summary['fire_detections']} | Smoke: {summary['smoke_detections']}"
                )
            else:
                failed_count += 1
                print(f"  ✗ FAILED: {summary.get('error', 'Unknown failure')}")

        except Exception as e:
            failed_count += 1
            print(f"\n  ✗ EXCEPTION on {vname}: {e}")
            results.append({
                "video_name": vname,
                "input_path": vpath,
                "status": "FAILED",
                "error": str(e),
            })

        print("-" * 70)

    overall_elapsed = time.perf_counter() - overall_start

    print("\n" + "=" * 70)
    print("  SAFESYNC P0 VIDEO ANALYSIS BATCH COMPLETE")
    print("=" * 70)
    print(f"  Total Videos Scanned   : {len(video_files)}")
    print(f"  Successfully Processed : {successful_count}")
    print(f"  Failed                 : {failed_count}")
    print(f"  Total Batch Time       : {overall_elapsed:.1f}s ({overall_elapsed/60:.2f} mins)")
    print("=" * 70 + "\n")

    # Output listing
    print("Generated Artifacts in output folder:")
    for res in results:
        status_sym = "✓" if res.get("status") == "COMPLETED" else "✗"
        print(f"  {status_sym} {res.get('video_name')}")
        if res.get("status") == "COMPLETED":
            print(f"      -> Video  : {res.get('output_path')}")
            print(f"      -> Summary: {os.path.splitext(res.get('output_path'))[0].replace('_annotated', '')}_summary.json")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
