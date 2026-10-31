"""
PMax Sentry Pro - Polar.sh Release Packager & Distribution Generator

Builds all wheels, bundles them with the Cursor/Claude Agent Skill and offline install scripts,
and produces a distribution ZIP artifact with SHA256 checksums ready for Polar.sh benefit download.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
POLAR_DIR = ROOT_DIR / "polar_upload"
DIST_DIR = POLAR_DIR / "dist"
VERSION = "0.1.0"
BUNDLE_NAME = f"pmax-sentry-pro-{VERSION}-bundle"


def calculate_sha256(filepath: Path) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


def build_wheels() -> list[Path]:
    print("[*] Building package wheels...")
    packages = [
        ROOT_DIR / "packages" / "pmax_sentry_core",
        ROOT_DIR / "packages" / "pmax_sentry_cli",
        ROOT_DIR / "packages" / "pmax_sentry_pro",
        ROOT_DIR / "packages" / "pmax_sentry_mcp",
    ]
    built_wheels: list[Path] = []
    wheel_staging = POLAR_DIR / "staging_wheels"
    if wheel_staging.exists():
        shutil.rmtree(wheel_staging)
    wheel_staging.mkdir(parents=True, exist_ok=True)

    for pkg in packages:
        print(f"  -> Building {pkg.name}...")
        cmd = [sys.executable, "-m", "build", "--wheel", "--outdir", str(wheel_staging), str(pkg)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error building {pkg.name}:\n{res.stderr}")
            sys.exit(1)

    built_wheels = list(wheel_staging.glob("*.whl"))
    print(f"[OK] Built {len(built_wheels)} wheels in {wheel_staging.name}")
    return built_wheels


def create_bundle(wheels: list[Path]) -> Path:
    print("[*] Creating distribution bundle...")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    bundle_zip = DIST_DIR / f"{BUNDLE_NAME}.zip"

    # Temporary staging directory for bundle content
    staging = POLAR_DIR / "staging_bundle"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    # 1. Copy wheels
    wheels_dest = staging / "wheels"
    wheels_dest.mkdir()
    for whl in wheels:
        shutil.copy2(whl, wheels_dest / whl.name)

    # 2. Copy Skill
    skill_dest = staging / "skill" / "pmax-delivery-audit"
    skill_dest.mkdir(parents=True)
    skill_src = ROOT_DIR / "skills" / "pmax-delivery-audit" / "SKILL.md"
    if skill_src.exists():
        shutil.copy2(skill_src, skill_dest / "SKILL.md")

    # 3. Create install scripts
    install_bat = staging / "install.bat"
    install_bat.write_text(
        "@echo off\n"
        "echo [*] Installing PMax Sentry Pro suite...\n"
        "python -m pip install --upgrade pip\n"
        "python -m pip install wheels\\*.whl\n"
        "echo [OK] Installation complete!\n"
        "echo Activate your license with: pmax-audit license activate <YOUR_POLAR_KEY>\n",
        encoding="utf-8",
    )

    install_sh = staging / "install.sh"
    install_sh.write_text(
        "#!/usr/bin/env bash\n"
        "set -e\n"
        "echo '[*] Installing PMax Sentry Pro suite...'\n"
        "python3 -m pip install --upgrade pip\n"
        "python3 -m pip install wheels/*.whl\n"
        "echo '[OK] Installation complete!'\n"
        "echo 'Activate your license with: pmax-audit license activate <YOUR_POLAR_KEY>'\n",
        encoding="utf-8",
    )

    # 4. Create README / Quickstart
    readme = staging / "README.md"
    readme.write_text(
        f"# PMax Sentry Pro v{VERSION}\n\n"
        "Welcome to PMax Sentry Pro! This bundle contains your agency tool suite and AI Agent Skill.\n\n"
        "## Quick Start\n\n"
        "1. **Install Wheels**:\n"
        "   - Windows: Run `install.bat`\n"
        "   - macOS/Linux: Run `bash install.sh`\n"
        "   - Or manual: `pip install wheels/*.whl`\n\n"
        "2. **Activate Your Polar License Key**:\n"
        "   ```bash\n"
        "   pmax-audit license activate <YOUR_POLAR_KEY>\n"
        "   ```\n"
        "   Verify with:\n"
        "   ```bash\n"
        "   pmax-audit license status\n"
        "   ```\n\n"
        "3. **AI Agent Setup (Cursor, Claude Desktop, Antigravity)**:\n"
        "   - Copy `skill/pmax-delivery-audit/SKILL.md` to `.agent/skills/pmax-delivery-audit/SKILL.md` in your project.\n"
        "   - To launch the MCP Server in Claude Desktop or Cursor:\n"
        "     Command: `pmax-mcp`\n\n"
        "4. **Generate White-Label Client Pitch Deck**:\n"
        "   ```bash\n"
        "   pmax-audit report --customer-id 1234567890 --dry-run --deck client_pitch_deck.html --agency \"Your Agency\" --brand \"Prospect Brand\"\n"
        "   ```\n",
        encoding="utf-8",
    )

    # 5. Build ZIP
    if bundle_zip.exists():
        bundle_zip.unlink()

    with zipfile.ZipFile(bundle_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in staging.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(staging)
                zf.write(file_path, arcname)

    # 6. Generate Checksum
    checksum = calculate_sha256(bundle_zip)
    checksum_file = DIST_DIR / f"{BUNDLE_NAME}.zip.sha256"
    checksum_file.write_text(f"{checksum}  {bundle_zip.name}\n", encoding="utf-8")

    # Cleanup staging
    shutil.rmtree(staging)
    shutil.rmtree(POLAR_DIR / "staging_wheels")

    print(f"\n[OK] Distribution bundle created successfully!")
    print(f"  Artifact:  {bundle_zip}")
    print(f"  Size:      {bundle_zip.stat().st_size / 1024:.1f} KB")
    print(f"  SHA256:    {checksum}")
    print(f"\nYou can upload this zip file to your Polar.sh 'Downloadable File' product benefit.")
    return bundle_zip


if __name__ == "__main__":
    wheels = build_wheels()
    create_bundle(wheels)
