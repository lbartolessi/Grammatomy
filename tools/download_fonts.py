"""
Font Downloader for Grammatomy.
Ensures 'Resource Sovereignty' by fetching fonts locally.
"""

import io
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

# Configuration
WEB_ROOT = Path(__file__).parent.parent / "src" / "web"
FONTS_DIR = WEB_ROOT / "public" / "fonts"

# Using google-webfonts-helper (gwfh) for stable ZIP downloads of WOFF2 files
FONTS = {
    "Roboto": "https://gwfh.mranftl.com/api/fonts/roboto?download=zip&subsets=latin&variants=regular,700&formats=woff2",
    "Roboto Mono": "https://gwfh.mranftl.com/api/fonts/roboto-mono?download=zip&subsets=latin&variants=regular,700&formats=woff2",
    "Charis SIL": "https://software.sil.org/downloads/r/charis/Charis-7.000.zip",
}

# Material Symbols Outlined (Variable Font)
ICON_FONT_URL = "https://github.com/google/material-design-icons/raw/master/variablefont/MaterialSymbolsOutlined%5BFILL,GRAD,opsz,wght%5D.ttf"


def download_and_extract(name, url, target_dir):
    print(f"⬇️  Downloading {name}...")
    try:
        # Add User-Agent to avoid 403/HTML responses from Google/GitHub
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req) as response:
            data = response.read()

        # If it's a zip (Families)
        if url.endswith(".zip") or "download=zip" in url:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                # DEBUG: Print zip contents to diagnose filename mismatches
                print(f"   [DEBUG] Zip contents: {[f.filename for f in z.infolist()]}")
                for file_info in z.infolist():
                    filename = os.path.basename(file_info.filename)
                    lower_name = filename.lower()

                    # Logic to rename and normalize files
                    target_name = None

                    # Charis SIL (TTF)
                    if "charis" in lower_name and filename.endswith(".ttf"):
                        if "regular" in lower_name:
                            target_name = "CharisSIL-Regular.ttf"
                        elif (
                            "bold" in lower_name
                            and "it" not in lower_name
                            and "semi" not in lower_name
                        ):
                            target_name = "CharisSIL-Bold.ttf"

                    # Roboto (WOFF2 from gwfh)
                    elif (
                        "roboto" in lower_name
                        and "mono" not in lower_name
                        and filename.endswith(".woff2")
                    ):
                        if (
                            "regular" in lower_name
                            or "400" in lower_name
                            or "normal" in lower_name
                        ):
                            target_name = "Roboto-Regular.woff2"
                        elif "bold" in lower_name or "700" in lower_name:
                            target_name = "Roboto-Bold.woff2"
                        else:
                            print(f"   [DEBUG] Skipped Roboto file: {filename}")

                    # Roboto Mono (WOFF2 from gwfh)
                    elif (
                        "roboto" in lower_name
                        and "mono" in lower_name
                        and filename.endswith(".woff2")
                    ):
                        if (
                            "regular" in lower_name
                            or "400" in lower_name
                            or "normal" in lower_name
                        ):
                            target_name = "RobotoMono-Regular.woff2"
                        elif "bold" in lower_name or "700" in lower_name:
                            target_name = "RobotoMono-Bold.woff2"
                        else:
                            print(f"   [DEBUG] Skipped Roboto Mono file: {filename}")

                    if target_name:
                        source = z.open(file_info)
                        target_path = target_dir / target_name
                        with open(target_path, "wb") as f_out:
                            shutil.copyfileobj(source, f_out)
                        print(f"   -> Extracted: {target_name}")

        # If it's a direct file (Icons)
        else:
            if "MaterialSymbols" in url:
                filename = "MaterialSymbolsOutlined.ttf"
            else:
                # Infer filename for other direct downloads (e.g. CharisSIL-Regular.ttf)
                filename = os.path.basename(url)

            target_path = target_dir / filename
            with open(target_path, "wb") as f:
                f.write(data)

        print(f"✅ {name} installed.")

    except Exception as e:
        print(f"❌ Failed to download {name}: {e}")


def main():
    if not WEB_ROOT.exists():
        print(f"Error: Web directory not found at {WEB_ROOT}")
        return

    # Create directory structure
    if FONTS_DIR.exists():
        shutil.rmtree(FONTS_DIR)
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📂 Created font directory: {FONTS_DIR}")

    # Download Families
    for name, url in FONTS.items():
        download_and_extract(name, url, FONTS_DIR)

    # Download Icons
    download_and_extract("Material Symbols", ICON_FONT_URL, FONTS_DIR)

    print("\n🎉 All fonts downloaded. Resource Sovereignty achieved.")
    print("   Remember to restart Vite if it's running.")


if __name__ == "__main__":
    main()
