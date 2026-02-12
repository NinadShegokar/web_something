import json
from pathlib import Path

RESULTS_DIR = Path("./results")
OUTPUT_DIR = Path("./parsed_docs")

OUTPUT_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# NMAP
# --------------------------------------------------
def parse_nmap():
    nmap_file = RESULTS_DIR / "nmap" / "nmap.txt"
    if not nmap_file.exists():
        return

    findings = []

    with open(nmap_file) as f:
        for line in f:
            if "/tcp" in line and "open" in line:
                parts = line.split()
                if len(parts) >= 4:
                    findings.append(
                        f"- Port: {parts[0]}, Service: {parts[2]}, Version: {parts[3]}"
                    )

    content = ["Tool: Nmap", "", "Findings:"]
    content.extend(findings if findings else ["No open ports detected."])

    (OUTPUT_DIR / "nmap_findings.txt").write_text("\n".join(content))


# --------------------------------------------------
# NUCLEI (BACKBONE – FULL CONTEXT, NO MATCHERS)
# --------------------------------------------------
def parse_nuclei():
    nuclei_file = RESULTS_DIR / "nuclei" / "nuclei.jsonl"
    if not nuclei_file.exists():
        return

    severity_map = {}

    with open(nuclei_file) as f:
        for line in f:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            info = item.get("info", {})

            severity = info.get("severity", "unknown")
            name = info.get("name", "Unnamed finding")
            description = info.get("description", "No description provided.")
            tags = info.get("tags", [])
            tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)

            target = (
                item.get("matched-at")
                or item.get("host")
                or item.get("url")
                or "Not specified"
            )

            finding_block = [
                f"- Name: {name}",
                f"  Description: {description}",
                f"  Target: {target}",
                f"  Tags: {tags_str}"
            ]

            severity_map.setdefault(severity, []).append("\n".join(finding_block))

    for severity, findings in severity_map.items():
        content = [
            "Tool: Nuclei",
            f"Severity: {severity}",
            "",
            "Findings:",
            ""
        ]

        for block in findings:
            content.append(block)
            content.append("")

        (OUTPUT_DIR / f"nuclei_{severity}.txt").write_text("\n".join(content).strip())


# --------------------------------------------------
# DIRSEARCH
# --------------------------------------------------
def parse_dirsearch():
    dirsearch_file = RESULTS_DIR / "dirsearch.txt"
    if not dirsearch_file.exists():
        return

    content = ["Tool: Dirsearch", "", "Findings:"]

    if dirsearch_file.stat().st_size == 0:
        content.append("No accessible directories or files discovered.")
    else:
        with open(dirsearch_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    content.append(f"- {line}")

    (OUTPUT_DIR / "dirsearch_findings.txt").write_text("\n".join(content))


# --------------------------------------------------
# NIKTO
# --------------------------------------------------
def parse_nikto():
    nikto_file = RESULTS_DIR / "nikto" / "nikto.txt"
    if not nikto_file.exists():
        return

    content = ["Tool: Nikto", "", "Findings:"]

    if nikto_file.stat().st_size == 0:
        content.append("No findings reported.")
    else:
        with open(nikto_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    content.append(f"- {line}")

    (OUTPUT_DIR / "nikto_findings.txt").write_text("\n".join(content))


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    if not RESULTS_DIR.exists():
        print("No results directory found. Nothing to parse.")
        return

    parse_nmap()
    parse_nuclei()
    parse_dirsearch()
    parse_nikto()

    print("Parsing complete. Detailed factual findings saved in ./parsed_docs/")


if __name__ == "__main__":
    main()
