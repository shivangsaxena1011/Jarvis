"""
SHIVANI Portable Distribution Builder
Packs build artifacts into a standalone portable ZIP distribution and computes SHA-256 checksum.
"""

import hashlib
import os
from pathlib import Path
import shutil
import zipfile


def compute_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def build_portable_package(source_dir: Path, output_zip: Path, version: str = "1.0.0") -> Path:
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    # Launcher batch script
    launcher_bat = source_dir / "run_portable.bat"
    with open(launcher_bat, "w") as f:
        f.write("@echo off\n")
        f.write("title SHIVANI Autonomous Agent\n")
        f.write("Shivani.exe %*\n")

    print(f"Creating portable zip: {output_zip} ...")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(source_dir)
                zipf.write(full_path, arcname=f"Shivani-{version}/{rel_path}")

    # Generate checksum
    checksum = compute_sha256(output_zip)
    checksum_file = output_zip.parent / f"{output_zip.stem}.sha256"
    with open(checksum_file, "w") as f:
        f.write(f"{checksum}  {output_zip.name}\n")

    print(f"Portable distribution created successfully!")
    print(f"Archive  : {output_zip}")
    print(f"SHA-256  : {checksum}")
    return output_zip


if __name__ == "__main__":
    src = Path("dist/Shivani")
    out = Path("dist/portable/Shivani-1.0.0-windows-x64.zip")
    if not src.exists():
        print(f"Source directory {src} does not exist. Run PyInstaller first.")
    else:
        build_portable_package(src, out)
