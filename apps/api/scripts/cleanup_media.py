"""
Media & Temporary File Cleanup CLI Tool for Japanese Speaking Training OS.
Scans and cleans orphaned/stale audio files in the temp directory.
Supports dry-run (default) and --apply flag.
"""

import argparse
import glob
import os
import sys
import tempfile
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def cleanup_temp_media(dry_run: bool = True, max_age_hours: float = 2.0) -> int:
    print("=" * 60)
    print(f" Media Cleanup Tool [{'DRY RUN' if dry_run else 'APPLY MODE'}]")
    print(f" Target: Temporary audio files older than {max_age_hours} hours")
    print("=" * 60)

    temp_dir = tempfile.gettempdir()
    patterns = [
        os.path.join(temp_dir, "tmp*.wav"),
        os.path.join(temp_dir, "whisper_*.wav"),
        os.path.join(temp_dir, "voicevox_*.wav"),
    ]

    now = time.time()
    cutoff_time = now - (max_age_hours * 3600)

    total_scanned = 0
    stale_files = []
    total_bytes = 0

    for pattern in patterns:
        for fpath in glob.glob(pattern):
            total_scanned += 1
            try:
                mtime = os.path.getmtime(fpath)
                if mtime < cutoff_time:
                    size = os.path.getsize(fpath)
                    stale_files.append((fpath, size, mtime))
                    total_bytes += size
            except Exception:
                pass

    print(f"Scanned {total_scanned} temporary files in '{temp_dir}'.")
    print(f"Found {len(stale_files)} stale files ({total_bytes / 1024:.1f} KB).")

    if not stale_files:
        print("[OK] No stale files found to clean.")
        return 0

    for fpath, size, mtime in stale_files[:10]:
        age_min = (now - mtime) / 60
        print(f"  - {os.path.basename(fpath)} ({size} bytes, {age_min:.0f} mins old)")

    if len(stale_files) > 10:
        print(f"  ... and {len(stale_files) - 10} more files.")

    if dry_run:
        print("\n[INFO] Dry-run mode: no files were deleted. Pass '--apply' to delete.")
    else:
        deleted = 0
        for fpath, _, _ in stale_files:
            try:
                os.remove(fpath)
                deleted += 1
            except Exception as e:
                print(f"[WARN] Failed to remove {fpath}: {e}")
        print(f"\n[OK] Successfully deleted {deleted} stale media files.")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean stale temporary audio files.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete files (default is dry run).",
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=2.0,
        help="Age threshold in hours for stale files (default: 2.0).",
    )
    args = parser.parse_args()

    sys.exit(cleanup_temp_media(dry_run=not args.apply, max_age_hours=args.max_age_hours))
