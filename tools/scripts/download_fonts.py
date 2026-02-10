"""
Font Downloader for Grammatomy.
Ensures 'Resource Sovereignty' by fetching fonts locally.
"""

import io
import logging
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

# Configuration
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

WEB_ROOT = Path(__file__).parent.parent / "src" / "web"
FONTS_DIR = WEB_ROOT / "public" / "fonts"

# Using google-webfonts-helper (gwfh) for stable ZIP downloads of WOFF2 files
FONTS = {
    "Roboto": (
        "https://gwfh.mranftl.com/api/fonts/roboto?download=zip&subsets=latin"
        "&variants=regular,700&formats=woff2"
    ),
    "Roboto Mono": (
        "https://gwfh.mranftl.com/api/fonts/roboto-mono?download=zip&subsets=latin"
        "&variants=regular,700&formats=woff2"
    ),
    "Charis SIL": "https://software.sil.org/downloads/r/charis/Charis-7.000.zip",
}

# Material Symbols Outlined (Variable Font)
ICON_FONT_URL = (
    "https://github.com/google/material-design-icons/raw/master/variablefont/"
    "MaterialSymbolsOutlined%5BFILL,GRAD,opsz,wght%5D.ttf"
)


def _match_charis(lower_name):
    if "charis" in lower_name and lower_name.endswith(".ttf"):
        if "regular" in lower_name:
            return "CharisSIL-Regular.ttf"
        if "bold" in lower_name and "it" not in lower_name and "semi" not in lower_name:
            return "CharisSIL-Bold.ttf"
    return None


def _match_roboto(lower_name, filename):
    if "roboto" in lower_name and "mono" not in lower_name and lower_name.endswith(".woff2"):
        if "regular" in lower_name or "400" in lower_name or "normal" in lower_name:
            return "Roboto-Regular.woff2"
        if "bold" in lower_name or "700" in lower_name:
            return "Roboto-Bold.woff2"
        logger.debug("   [DEBUG] Skipped Roboto file: %s", filename)
    return None


def _match_roboto_mono(lower_name, filename):
    if "roboto" in lower_name and "mono" in lower_name and lower_name.endswith(".woff2"):
        if "regular" in lower_name or "400" in lower_name or "normal" in lower_name:
            return "RobotoMono-Regular.woff2"
        if "bold" in lower_name or "700" in lower_name:
            return "RobotoMono-Bold.woff2"
        logger.debug("   [DEBUG] Skipped Roboto Mono file: %s", filename)
    return None


def _get_target_filename(filename):
    """Determines the target filename based on the source filename."""
    lower_name = filename.lower()
    return (
        _match_charis(lower_name)
        or _match_roboto(lower_name, filename)
        or _match_roboto_mono(lower_name, filename)
    )


def _process_zip_file(data, target_dir):
    """Extracts specific fonts from a zip archive."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        # DEBUG: Print zip contents to diagnose filename mismatches
        logger.debug("   [DEBUG] Zip contents: %s", [f.filename for f in z.infolist()])
        for file_info in z.infolist():
            filename = os.path.basename(file_info.filename)
            target_name = _get_target_filename(filename)

            if target_name:
                source = z.open(file_info)
                target_path = target_dir / target_name
                with open(target_path, "wb") as f_out:
                    shutil.copyfileobj(source, f_out)
                logger.info("   -> Extracted: %s", target_name)


def download_and_extract(name, url, target_dir):
    logger.info("⬇️  Downloading %s...", name)
    try:
        # Add User-Agent to avoid 403/HTML responses from Google/GitHub
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req) as response:
            data = response.read()

        # If it's a zip (Families)
        if url.endswith(".zip") or "download=zip" in url:
            _process_zip_file(data, target_dir)

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

        logger.info("✅ %s installed.", name)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("❌ Failed to download %s: %s", name, e)


def main():
    if not WEB_ROOT.exists():
        logger.error("Error: Web directory not found at %s", WEB_ROOT)
        return

    # Create directory structure
    if FONTS_DIR.exists():
        shutil.rmtree(FONTS_DIR)
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("📂 Created font directory: %s", FONTS_DIR)

    # Download Families
    for name, url in FONTS.items():
        download_and_extract(name, url, FONTS_DIR)

    # Download Icons
    download_and_extract("Material Symbols", ICON_FONT_URL, FONTS_DIR)

    logger.info("\n🎉 All fonts downloaded. Resource Sovereignty achieved.")
    logger.info("   Remember to restart Vite if it's running.")


if __name__ == "__main__":
    main()
