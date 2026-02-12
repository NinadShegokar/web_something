#!/usr/bin/env python3

import sys

import scans
import parser
import rag_index
import rag_query


def main():
    # -----------------------------
    # 1. Run scans
    # -----------------------------
    print("\n[STEP 1] Running scans...\n")
    target = "https://sih.gov.in/"  # change if needed
    scans.run_all_scans(target)

    # -----------------------------
    # 2. Parse scan results
    # -----------------------------
    print("\n[STEP 2] Parsing scan results...\n")
    parser.main()

    # -----------------------------
    # 3. Build RAG index
    # -----------------------------
    print("\n[STEP 3] Building RAG index...\n")
    rag_index.main()

    # -----------------------------
    # 4. Query (interactive)
    # -----------------------------
    print("\n[STEP 4] Ready for queries\n")
    while True:
        try:
            q = input("Ask a question (or 'exit'): ").strip()
            if q.lower() in {"exit", "quit"}:
                break
            answer = rag_query.ask(q)
            print("\n" + answer + "\n")
        except KeyboardInterrupt:
            break

    print("\n[PIPELINE] Finished\n")


if __name__ == "__main__":
    main()
