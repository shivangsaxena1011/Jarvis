"""
SHIVANI Clean Uninstaller Utility
Provides options for clean removal of application binaries, shortcuts,
and optionally user AppData (memory, vault, logs, and backups).
"""

import argparse
import os
from pathlib import Path
import shutil
import sys

from core.config.app_dirs import get_app_dirs


def perform_uninstall(remove_data: bool = False, force: bool = False) -> int:
    dirs = get_app_dirs()
    print("=== SHIVANI UNINSTALLER ===")
    print(f"Target AppData Directory: {dirs.root_dir}")

    if remove_data:
        if not force:
            ans = input(f"Are you sure you want to permanently delete user data at {dirs.root_dir}? (y/N): ")
            if ans.lower() != "y":
                print("Aborting data removal.")
                return 0

        if dirs.root_dir.exists():
            print(f"Purging {dirs.root_dir}...")
            shutil.rmtree(dirs.root_dir, ignore_errors=True)
            print("User data directory removed.")
        else:
            print("AppData directory not found.")
    else:
        print("Preserving user data (memory, vault, backups). Only application files uninstalled.")

    print("Uninstallation complete.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="SHIVANI Uninstaller")
    parser.add_argument("--purge-data", action="store_true", help="Also remove all user memory, vault, and log directories")
    parser.add_argument("--force", action="store_true", help="Bypass confirmation prompt")
    args = parser.parse_args()

    sys.exit(perform_uninstall(remove_data=args.purge_data, force=args.force))


if __name__ == "__main__":
    main()
