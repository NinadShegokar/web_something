#!/usr/bin/env python3

import subprocess
import shutil
import re
from pathlib import Path

# --------------------------------------------------
# Setup
# --------------------------------------------------
BASE_RESULTS = Path("./results")
BASE_RESULTS.mkdir(exist_ok=True)


# --------------------------------------------------
# Utilities
# --------------------------------------------------
def normalize_target(url: str) -> str:
    if url.startswith(("http://", "https://")):
        return re.sub(r"^https?://", "", url).split("/")[0]
    return url


def run_tool(name, cmd, output_file=None, timeout=600):
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )

    except subprocess.TimeoutExpired:
        if output_file and output_file.exists() and output_file.stat().st_size > 0:
            size = output_file.stat().st_size
            print(f"[{name}] PARTIAL | output={size} bytes (timeout)")
        else:
            print(f"[{name}] ERROR | timeout after {timeout}s")
        return

    except FileNotFoundError:
        print(f"[{name}] ERROR | binary not found")
        return

    if output_file and output_file.exists():
        size = output_file.stat().st_size
        if size > 0:
            print(f"[{name}] OK | output={size} bytes")
            return
        else:
            print(f"[{name}] WARN | output file empty")
            return

    print(f"[{name}] OK")


# --------------------------------------------------
# NMAP (light)
# --------------------------------------------------
def run_nmap(target_url: str):
    if not shutil.which("nmap"):
        print("[NMAP] ERROR | not installed")
        return

    target = normalize_target(target_url)
    output_dir = BASE_RESULTS / "nmap"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "nmap.txt"

    cmd = [
        "nmap",
        "-T4",
        "--top-ports", "1000",
        "-sV",
        "-oN", str(output_file),
        target
    ]

    run_tool("NMAP", cmd, output_file, timeout=900)


# --------------------------------------------------
# DIRSEARCH (safe flags)
# --------------------------------------------------
def run_dirsearch(target_url: str):
    dirsearch_path = Path("./dirsearch/dirsearch.py")

    if not dirsearch_path.exists():
        print("[DIRSEARCH] ERROR | dirsearch.py not found at ./dirsearch/")
        return

    output_file = BASE_RESULTS / "dirsearch.txt"

    cmd = [
        "python3",
        str(dirsearch_path),
        "-u", target_url,
        "-e", "php,html,txt",
        "--exclude-status", "404",
        "--random-agent",
        "--force",
        "-o", str(output_file)
    ]

    run_tool("DIRSEARCH", cmd, output_file, timeout=600)


# --------------------------------------------------
# NIKTO (tuned)
# --------------------------------------------------
def run_nikto(target_url: str):
    if not shutil.which("nikto"):
        print("[NIKTO] ERROR | not installed")
        return

    output_dir = BASE_RESULTS / "nikto"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "nikto.txt"

    cmd = [
        "nikto",
        "-h", target_url,
        "-Tuning", "x6",
        "-o", str(output_file),
        "-Format", "txt"
    ]

    run_tool("NIKTO", cmd, output_file, timeout=1500)


# --------------------------------------------------
# NUCLEI (unchanged – already optimal)
# --------------------------------------------------
def run_nuclei(target_url: str):
    if not shutil.which("nuclei"):
        print("[NUCLEI] ERROR | not installed")
        return

    output_dir = BASE_RESULTS / "nuclei"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "nuclei.jsonl"

    cmd = [
        "nuclei",
        "-u", target_url,
        "-severity", "critical,high,medium,low,info",
        "-jsonl",
        "-o", str(output_file),
        "-silent"
    ]

    run_tool("NUCLEI", cmd, output_file, timeout=600)


# --------------------------------------------------
# PIPELINE
# --------------------------------------------------
def run_all_scans(target_url: str):
    print(f"\n[PIPELINE] Target: {target_url}\n")

    run_nmap(target_url)
    run_dirsearch(target_url)
    run_nikto(target_url)
    run_nuclei(target_url)

    print("\n[PIPELINE] Done\n")


if __name__ == "__main__":
    target = "http://testphp.vulnweb.com"
    run_all_scans(target)
