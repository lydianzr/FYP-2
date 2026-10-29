# scripts/download_datasets.py
import os
import shutil
import zipfile
import urllib.request
import argparse
import subprocess

# --- Path Configurations ---
RAW_DIR = "data/raw"

# FUNSD Configurations
FUNSD_DIR = os.path.join(RAW_DIR, "funsd")
FUNSD_ZIP = os.path.join(RAW_DIR, "funsd.zip")
FUNSD_URL = "https://www.crc.nd.edu/~pmoreira/funsd.zip"

# DocILE Configurations
DOCILE_SCRIPT_URL = "https://raw.githubusercontent.com/rossumai/docile/main/download_dataset.sh"
DOCILE_SCRIPT_PATH = "download_dataset.sh"
DOCILE_DIR = os.path.join(RAW_DIR, "docile")

def download_funsd():
    """Step 1: Download and extract FUNSD dataset."""
    os.makedirs(RAW_DIR, exist_ok=True)
    
    if os.path.exists(FUNSD_DIR) and len(os.listdir(FUNSD_DIR)) > 0:
        print("[1/2 FUNSD] Dataset already downloaded. Skipping.")
        return

    print(f"[1/2 FUNSD] Downloading from {FUNSD_URL}...")
    urllib.request.urlretrieve(FUNSD_URL, FUNSD_ZIP)
    
    print("[1/2 FUNSD] Extracting zip archive...")
    with zipfile.ZipFile(FUNSD_ZIP, "r") as zip_ref:
        zip_ref.extractall(FUNSD_DIR)
        
    os.remove(FUNSD_ZIP)
    print("[1/2 FUNSD] Download and extraction complete.")

def download_docile(token=None):
    """Step 2: Download and extract DocILE dataset via official shell script."""
    docile_token = token or os.getenv("DOCILE_TOKEN")
    
    # Check if DocILE PDFs are already present
    if os.path.exists(DOCILE_DIR):
        existing_files = [f for root, _, files in os.walk(DOCILE_DIR) for f in files if f.endswith(".pdf")]
        if len(existing_files) > 0:
            print("[2/2 DocILE] Dataset PDFs already detected. Skipping.")
            return

    if not docile_token:
        print("\n" + "="*60)
        print("[2/2 DocILE] ERROR: Missing Access Token!")
        print("Please add DOCILE_TOKEN=your_token to your .env file or run:")
        print("  python scripts/download_datasets.py --token <YOUR_TOKEN>")
        print("="*60 + "\n")
        return

    # Download official downloader script if missing locally
    if not os.path.exists(DOCILE_SCRIPT_PATH):
        print("[2/2 DocILE] Fetching download_dataset.sh from GitHub...")
        urllib.request.urlretrieve(DOCILE_SCRIPT_URL, DOCILE_SCRIPT_PATH)

    # Resolve bash executable for Windows (PowerShell/CMD) and Linux/macOS
    bash_bin = shutil.which("bash") or r"C:\Program Files\Git\bin\bash.exe"
    
    if os.name == "nt" and os.path.exists(bash_bin):
        cmd = [bash_bin, "download_dataset.sh", docile_token, "annotated-trainval", "data/raw/docile", "--unzip"]
    else:
        cmd = ["bash", "download_dataset.sh", docile_token, "annotated-trainval", "data/raw/docile", "--unzip"]

    print(f"[2/2 DocILE] Downloading dataset using token: {docile_token[:4]}****...")
    try:
        subprocess.run(cmd, check=True)
        print("[2/2 DocILE] Download and extraction complete.")
    except Exception as e:
        print(f"[2/2 DocILE] Execution failed: {e}")

if __name__ == "__main__":
    # Load .env file automatically
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description="Consolidated Dataset Downloader (FUNSD + DocILE)")
    parser.add_argument("--token", help="DocILE access token", default=None)
    args = parser.parse_args()

    print("=== Starting Consolidated Dataset Download ===")
    download_funsd()
    download_docile(args.token)
    print("=== All Dataset Setup Tasks Completed ===")